import asyncio
if not hasattr(asyncio, 'Runner'):
    asyncio.Runner = object

import unittest
from app import create_app
from extensions import db
from models import User, TutorProfile, Subject, TuitionRequest, TuitionRequirement, RequirementResponse
from seed import DEFAULT_SUBJECTS, seed_database


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        class TestConfig:
            TESTING = True
            SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
            SQLALCHEMY_TRACK_MODIFICATIONS = False
            SECRET_KEY = 'test-secret-key-12345'
            WTF_CSRF_ENABLED = False

        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

        db.create_all()
        # Seed subjects
        for name, category in DEFAULT_SUBJECTS:
            s = Subject(name=name, category=category)
            db.session.add(s)
        db.session.commit()

        # Create demo tutor
        self.tutor_user = User(
            full_name="Prof. Sharma",
            email="prof.sharma@example.com",
            role="tutor",
            city="Chennai"
        )
        self.tutor_user.set_password("SecurePassword123!")
        db.session.add(self.tutor_user)
        db.session.flush()

        self.tutor_profile = TutorProfile(
            user_id=self.tutor_user.id,
            headline="Expert Math Educator",
            biography="10 years of experience teaching calculus and algebra.",
            qualifications="M.Sc. Mathematics",
            experience_years=10,
            hourly_fee=1000,
            teaching_mode="Online",
            languages="English, Tamil",
            student_levels="High School, College",
            availability="Weekdays"
        )
        math_subj = Subject.query.filter_by(name="Mathematics").first()
        if math_subj:
            self.tutor_profile.subjects.append(math_subj)
        db.session.add(self.tutor_profile)

        # Create demo student
        self.student_user = User(
            full_name="Kavya Student",
            email="kavya@example.com",
            role="student",
            city="Chennai"
        )
        self.student_user.set_password("StudentPassword123!")
        db.session.add(self.student_user)
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()


class PageNavigationTests(BaseTestCase):
    def test_homepage_loads(self):
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"LearnBridge", res.data)
        self.assertIn(b"Find the Right Tutor for Every Learning Goal", res.data)
        self.assertIn(b"Mathematics", res.data)

    def test_static_pages_load(self):
        for route in ['/about', '/contact', '/privacy', '/terms']:
            res = self.client.get(route)
            self.assertEqual(res.status_code, 200)

    def test_healthz_endpoint(self):
        res = self.client.get('/healthz')
        self.assertEqual(res.status_code, 200)
        json_data = res.get_json()
        self.assertEqual(json_data['status'], 'healthy')
        self.assertEqual(json_data['database'], 'connected')

    def test_404_handler(self):
        res = self.client.get('/nonexistent-page-path')
        self.assertEqual(res.status_code, 404)
        self.assertIn(b"Page Not Found", res.data)


class AuthenticationTests(BaseTestCase):
    def test_student_registration_success(self):
        with self.client.session_transaction() as sess:
            sess['csrf_token'] = 'token123'

        res = self.client.post('/register', data={
            'csrf_token': 'token123',
            'full_name': 'Aarav Patel',
            'email': 'aarav@test.com',
            'city': 'Ahmedabad',
            'password': 'Password123!',
            'confirm_password': 'Password123!'
        }, follow_redirects=True)

        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Welcome to LearnBridge, Aarav Patel!", res.data)
        user = User.query.filter_by(email='aarav@test.com').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.role, 'student')
        self.assertTrue(user.check_password('Password123!'))
        self.assertNotEqual(user.password_hash, 'Password123!')

    def test_duplicate_email_rejected(self):
        with self.client.session_transaction() as sess:
            sess['csrf_token'] = 'token123'

        res = self.client.post('/register', data={
            'csrf_token': 'token123',
            'full_name': 'Duplicate User',
            'email': 'kavya@example.com',
            'city': 'Chennai',
            'password': 'Password123!',
            'confirm_password': 'Password123!'
        }, follow_redirects=True)

        self.assertIn(b"already exists", res.data)

    def test_tutor_registration_success(self):
        with self.client.session_transaction() as sess:
            sess['csrf_token'] = 'token123'

        res = self.client.post('/become-tutor', data={
            'csrf_token': 'token123',
            'full_name': 'Dr. Sunita Rao',
            'email': 'sunita@test.com',
            'city': 'Bengaluru',
            'password': 'Password123!',
            'confirm_password': 'Password123!',
            'headline': 'Experienced Physics Lecturer',
            'biography': 'Over 8 years teaching high school physics and coaching for NEET.',
            'qualifications': 'Ph.D. in Physics (IISc)',
            'experience_years': '8',
            'hourly_fee': '1200',
            'teaching_mode': 'Both',
            'languages': 'English, Hindi',
            'student_levels': 'High School, College',
            'availability': 'Evenings'
        }, follow_redirects=True)

        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Welcome to LearnBridge, Dr. Sunita Rao!", res.data)
        tutor = User.query.filter_by(email='sunita@test.com').first()
        self.assertIsNotNone(tutor)
        self.assertEqual(tutor.role, 'tutor')
        self.assertEqual(tutor.tutor_profile.hourly_fee, 1200)

    def test_login_and_logout(self):
        with self.client.session_transaction() as sess:
            sess['csrf_token'] = 'token123'

        # Wrong password
        res_fail = self.client.post('/login', data={
            'csrf_token': 'token123',
            'email': 'kavya@example.com',
            'password': 'WrongPassword!'
        }, follow_redirects=True)
        self.assertIn(b"Invalid email or password", res_fail.data)

        # Correct password
        res_pass = self.client.post('/login', data={
            'csrf_token': 'token123',
            'email': 'kavya@example.com',
            'password': 'StudentPassword123!'
        }, follow_redirects=True)
        self.assertIn(b"Welcome back, Kavya Student!", res_pass.data)

        # Logout
        res_logout = self.client.post('/logout', data={'csrf_token': 'token123'}, follow_redirects=True)
        self.assertIn(b"You have been logged out successfully", res_logout.data)


class TutorDiscoveryTests(BaseTestCase):
    def test_tutors_listing_and_filters(self):
        res = self.client.get('/tutors')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Prof. Sharma", res.data)
        self.assertIn(b"Expert Math Educator", res.data)

        # Match filter
        res_filtered = self.client.get('/tutors?subject=Mathematics')
        self.assertEqual(res_filtered.status_code, 200)
        self.assertIn(b"Prof. Sharma", res_filtered.data)

        # Non match
        res_nomatch = self.client.get('/tutors?subject=NonExistentSubject')
        self.assertEqual(res_nomatch.status_code, 200)
        self.assertIn(b"No Tutors Match Your Current Filters", res_nomatch.data)

    def test_tutor_profile_view(self):
        res = self.client.get(f'/tutor/{self.tutor_profile.id}')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Prof. Sharma", res.data)
        self.assertIn(b"M.Sc. Mathematics", res.data)

        # Privacy check: private credentials must not be revealed
        self.assertNotIn(b"prof.sharma@example.com", res.data)
        self.assertNotIn(b"password_hash", res.data)


class TuitionRequestWorkflowTests(BaseTestCase):
    def test_full_request_workflow(self):
        # 1. Student sends request
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.student_user.id
            sess['user_role'] = 'student'
            sess['csrf_token'] = 'token123'

        math_subj = Subject.query.filter_by(name="Mathematics").first()

        res_send = self.client.post(f'/tutor/{self.tutor_profile.id}/request', data={
            'csrf_token': 'token123',
            'subject_id': str(math_subj.id),
            'student_level': 'Higher Secondary (Grade 11-12)',
            'teaching_mode': 'Online',
            'budget': '1000',
            'preferred_schedule': 'Mon, Wed 6 PM',
            'message': 'Need calculus guidance'
        }, follow_redirects=True)

        self.assertEqual(res_send.status_code, 200)
        self.assertIn(b"Your tuition enquiry has been sent", res_send.data)

        req = TuitionRequest.query.filter_by(student_id=self.student_user.id, tutor_id=self.tutor_profile.id).first()
        self.assertIsNotNone(req)
        self.assertEqual(req.status, 'pending')

        # 2. Tutor accepts request
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.tutor_user.id
            sess['user_role'] = 'tutor'
            sess['csrf_token'] = 'token123'

        res_accept = self.client.post(f'/tutor/request/{req.id}/status', data={
            'csrf_token': 'token123',
            'status': 'accepted'
        }, follow_redirects=True)

        self.assertEqual(res_accept.status_code, 200)
        self.assertIn(b"Request has been marked as accepted", res_accept.data)

        req_updated = db.session.get(TuitionRequest, req.id)
        self.assertEqual(req_updated.status, 'accepted')

        # 3. Student submits payment proof
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.student_user.id
            sess['user_role'] = 'student'
            sess['csrf_token'] = 'token123'

        res_pay = self.client.post(f'/student/request/{req.id}/pay', data={
            'csrf_token': 'token123',
            'payment_reference': 'UTR1234567890',
            'payment_notes': 'Paid via GPay'
        }, follow_redirects=True)
        self.assertEqual(res_pay.status_code, 200)
        self.assertIn(b"Payment details submitted", res_pay.data)

        req_paid = db.session.get(TuitionRequest, req.id)
        self.assertEqual(req_paid.payment_status, 'paid_submitted')
        self.assertEqual(req_paid.payment_reference, 'UTR1234567890')

        # 4. Tutor confirms payment received
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.tutor_user.id
            sess['user_role'] = 'tutor'
            sess['csrf_token'] = 'token123'

        res_confirm = self.client.post(f'/tutor/request/{req.id}/confirm-payment', data={
            'csrf_token': 'token123',
            'action': 'confirm'
        }, follow_redirects=True)
        self.assertEqual(res_confirm.status_code, 200)
        self.assertIn(b"Payment verified and confirmed", res_confirm.data)

        req_confirmed = db.session.get(TuitionRequest, req.id)
        self.assertEqual(req_confirmed.payment_status, 'payment_confirmed')

    def test_student_cancellation(self):
        req = TuitionRequest(
            student_id=self.student_user.id,
            tutor_id=self.tutor_profile.id,
            student_level='College',
            teaching_mode='Online',
            preferred_schedule='Weekends',
            budget=900,
            message='Calculus practice',
            status='pending'
        )
        db.session.add(req)
        db.session.commit()

        with self.client.session_transaction() as sess:
            sess['user_id'] = self.student_user.id
            sess['user_role'] = 'student'
            sess['csrf_token'] = 'token123'

        res = self.client.post(f'/student/request/{req.id}/cancel', data={
            'csrf_token': 'token123'
        }, follow_redirects=True)

        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Tuition request has been cancelled", res.data)
        req_cancelled = db.session.get(TuitionRequest, req.id)
        self.assertEqual(req_cancelled.status, 'cancelled')


class TuitionRequirementTests(BaseTestCase):
    def test_post_requirement_and_tutor_response(self):
        # 1. Student posts requirement
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.student_user.id
            sess['user_role'] = 'student'
            sess['csrf_token'] = 'token123'

        res_post = self.client.post('/find-tuition', data={
            'csrf_token': 'token123',
            'student_level': 'High School',
            'teaching_mode': 'Online',
            'location': 'Chennai',
            'budget': '800',
            'preferred_schedule': 'Evenings',
            'description': 'Looking for physics tuition for 10th grade'
        }, follow_redirects=True)

        self.assertEqual(res_post.status_code, 200)
        self.assertIn(b"Your tuition requirement has been posted successfully", res_post.data)

        req = TuitionRequirement.query.filter_by(student_id=self.student_user.id).first()
        self.assertIsNotNone(req)
        self.assertEqual(req.status, 'open')

        # 2. Tutor responds
        with self.client.session_transaction() as sess:
            sess['user_id'] = self.tutor_user.id
            sess['user_role'] = 'tutor'
            sess['csrf_token'] = 'token123'

        res_resp = self.client.post(f'/requirement/{req.id}/respond', data={
            'csrf_token': 'token123',
            'proposed_fee': '750',
            'message': 'I have coached 100+ high school students in physics.'
        }, follow_redirects=True)

        self.assertEqual(res_resp.status_code, 200)
        self.assertIn(b"Your proposal has been submitted to the student", res_resp.data)

        resp_entry = RequirementResponse.query.filter_by(requirement_id=req.id).first()
        self.assertIsNotNone(resp_entry)
        self.assertEqual(resp_entry.proposed_fee, 750)


if __name__ == '__main__':
    unittest.main()
