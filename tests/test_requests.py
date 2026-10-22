from models import TuitionRequest, Subject
from extensions import db


def test_send_and_accept_tuition_request(client, app, sample_student, sample_tutor):
    student_id = sample_student
    tutor_user_id, tutor_profile_id = sample_tutor

    with app.app_context():
        subj = Subject.query.filter_by(name="Mathematics").first()
        subj_id = subj.id if subj else 1

    # 1. Student logs in and sends request
    with client.session_transaction() as sess:
        sess['user_id'] = student_id
        sess['user_role'] = 'student'
        sess['csrf_token'] = 'test-token'

    res_send = client.post(f'/tutor/{tutor_profile_id}/request', data={
        'csrf_token': 'test-token',
        'subject_id': str(subj_id),
        'student_level': 'Higher Secondary (Grade 11-12)',
        'teaching_mode': 'Online',
        'budget': '1000',
        'preferred_schedule': 'Mon, Wed, Fri 6 PM',
        'message': 'Need help preparing for calculus board exam.'
    }, follow_redirects=True)

    assert res_send.status_code == 200
    assert b"Your tuition enquiry has been sent" in res_send.data

    with app.app_context():
        req = TuitionRequest.query.filter_by(student_id=student_id, tutor_id=tutor_profile_id).first()
        assert req is not None
        assert req.status == 'pending'
        req_id = req.id

    # 2. Tutor logs in and accepts request
    with client.session_transaction() as sess:
        sess['user_id'] = tutor_user_id
        sess['user_role'] = 'tutor'
        sess['csrf_token'] = 'test-token'

    res_accept = client.post(f'/tutor/request/{req_id}/status', data={
        'csrf_token': 'test-token',
        'status': 'accepted'
    }, follow_redirects=True)

    assert res_accept.status_code == 200
    assert b"Request has been marked as accepted" in res_accept.data

    with app.app_context():
        req_updated = db.session.get(TuitionRequest, req_id)
        assert req_updated.status == 'accepted'


def test_student_cancel_pending_request(client, app, sample_student, sample_tutor):
    student_id = sample_student
    tutor_user_id, tutor_profile_id = sample_tutor

    # Create a pending request
    with app.app_context():
        req = TuitionRequest(
            student_id=student_id,
            tutor_id=tutor_profile_id,
            student_level='High School',
            teaching_mode='Online',
            preferred_schedule='Weekends',
            budget=800,
            message='Looking for algebra help',
            status='pending'
        )
        db.session.add(req)
        db.session.commit()
        req_id = req.id

    # Student cancels
    with client.session_transaction() as sess:
        sess['user_id'] = student_id
        sess['user_role'] = 'student'
        sess['csrf_token'] = 'test-token'

    res_cancel = client.post(f'/student/request/{req_id}/cancel', data={
        'csrf_token': 'test-token'
    }, follow_redirects=True)

    assert res_cancel.status_code == 200
    assert b"Tuition request has been cancelled" in res_cancel.data

    with app.app_context():
        req_cancelled = db.session.get(TuitionRequest, req_id)
        assert req_cancelled.status == 'cancelled'


def test_cannot_cancel_others_request(client, app, sample_tutor):
    tutor_user_id, tutor_profile_id = sample_tutor

    # Create two students
    with app.app_context():
        from models import User
        student_a = User(full_name="Student A", email="a@test.com", role="student", city="Delhi")
        student_a.set_password("pass123")
        student_b = User(full_name="Student B", email="b@test.com", role="student", city="Delhi")
        student_b.set_password("pass123")
        db.session.add_all([student_a, student_b])
        db.session.flush()

        req = TuitionRequest(
            student_id=student_a.id,
            tutor_id=tutor_profile_id,
            student_level='High School',
            teaching_mode='Online',
            preferred_schedule='Weekends',
            budget=800,
            message='Test message',
            status='pending'
        )
        db.session.add(req)
        db.session.commit()
        req_id = req.id
        student_b_id = student_b.id

    # Student B attempts to cancel Student A's request
    with client.session_transaction() as sess:
        sess['user_id'] = student_b_id
        sess['user_role'] = 'student'
        sess['csrf_token'] = 'test-token'

    res = client.post(f'/student/request/{req_id}/cancel', data={
        'csrf_token': 'test-token'
    }, follow_redirects=True)

    assert b"unauthorized" in res.data.lower()

    with app.app_context():
        req_check = db.session.get(TuitionRequest, req_id)
        assert req_check.status == 'pending'  # untouched!
