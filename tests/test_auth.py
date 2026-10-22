from models import User
from extensions import db


def test_student_registration(client, app):
    # Get CSRF token
    with client.session_transaction() as sess:
        sess['csrf_token'] = 'test-token'

    response = client.post('/register', data={
        'csrf_token': 'test-token',
        'full_name': 'Aarav Gupta',
        'email': 'aarav@example.com',
        'city': 'Mumbai',
        'password': 'Password123!',
        'confirm_password': 'Password123!'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Welcome to LearnBridge, Aarav Gupta!" in response.data

    with app.app_context():
        user = User.query.filter_by(email='aarav@example.com').first()
        assert user is not None
        assert user.role == 'student'
        assert user.check_password('Password123!')
        assert user.password_hash != 'Password123!'  # Securely hashed


def test_duplicate_email_registration_rejected(client, sample_student):
    with client.session_transaction() as sess:
        sess['csrf_token'] = 'test-token'

    response = client.post('/register', data={
        'csrf_token': 'test-token',
        'full_name': 'Duplicate User',
        'email': 'kavya@example.com',  # Already exists from fixture
        'city': 'Chennai',
        'password': 'Password123!',
        'confirm_password': 'Password123!'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"already exists" in response.data


def test_tutor_registration(client, app):
    with client.session_transaction() as sess:
        sess['csrf_token'] = 'test-token'

    response = client.post('/become-tutor', data={
        'csrf_token': 'test-token',
        'full_name': 'Dr. Sunita Rao',
        'email': 'sunita@example.com',
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

    assert response.status_code == 200
    assert b"Welcome to LearnBridge, Dr. Sunita Rao!" in response.data

    with app.app_context():
        user = User.query.filter_by(email='sunita@example.com').first()
        assert user is not None
        assert user.role == 'tutor'
        assert user.tutor_profile is not None
        assert user.tutor_profile.hourly_fee == 1200


def test_login_and_logout(client, sample_student):
    with client.session_transaction() as sess:
        sess['csrf_token'] = 'test-token'

    # Bad password
    resp_fail = client.post('/login', data={
        'csrf_token': 'test-token',
        'email': 'kavya@example.com',
        'password': 'WrongPassword!'
    }, follow_redirects=True)
    assert b"Invalid email or password" in resp_fail.data

    # Good password
    resp_success = client.post('/login', data={
        'csrf_token': 'test-token',
        'email': 'kavya@example.com',
        'password': 'StudentPassword123!'
    }, follow_redirects=True)
    assert b"Welcome back, Kavya Student!" in resp_success.data

    # Logout
    resp_logout = client.post('/logout', data={'csrf_token': 'test-token'}, follow_redirects=True)
    assert b"You have been logged out successfully" in resp_logout.data


def test_role_based_access(client, sample_student, sample_tutor):
    # Anonymous cannot access student dashboard
    resp_anon = client.get('/student/dashboard', follow_redirects=True)
    assert b"Please log in to continue" in resp_anon.data

    # Log in as tutor, try to access student dashboard
    with client.session_transaction() as sess:
        sess['user_id'] = sample_tutor[0]
        sess['user_role'] = 'tutor'
        sess['csrf_token'] = 'test-token'

    resp_forbidden = client.get('/student/dashboard', follow_redirects=True)
    assert b"Access restricted to students only" in resp_forbidden.data
