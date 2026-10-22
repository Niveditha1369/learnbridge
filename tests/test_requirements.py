from models import TuitionRequirement, RequirementResponse
from extensions import db


def test_post_and_view_tuition_requirement(client, app, sample_student):
    with client.session_transaction() as sess:
        sess['user_id'] = sample_student
        sess['user_role'] = 'student'
        sess['csrf_token'] = 'test-token'

    # Student posts requirement
    response = client.post('/find-tuition', data={
        'csrf_token': 'test-token',
        'student_level': 'Higher Secondary (Grade 11-12)',
        'teaching_mode': 'Online',
        'location': 'Chennai',
        'budget': '900',
        'preferred_schedule': 'Tues, Thurs evenings',
        'description': 'Need comprehensive guidance for CBSE class 12 physics board exam.'
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Your tuition requirement has been posted successfully" in response.data

    with app.app_context():
        req = TuitionRequirement.query.filter_by(student_id=sample_student).first()
        assert req is not None
        assert req.status == 'open'
        assert req.budget == 900


def test_tutor_responds_to_requirement(client, app, sample_student, sample_tutor):
    tutor_user_id, tutor_profile_id = sample_tutor

    with app.app_context():
        req = TuitionRequirement(
            student_id=sample_student,
            student_level='College',
            teaching_mode='Online',
            location='Bengaluru',
            budget=1200,
            preferred_schedule='Weekends',
            description='Data structures coaching needed.',
            status='open'
        )
        db.session.add(req)
        db.session.commit()
        req_id = req.id

    # Tutor responds
    with client.session_transaction() as sess:
        sess['user_id'] = tutor_user_id
        sess['user_role'] = 'tutor'
        sess['csrf_token'] = 'test-token'

    res = client.post(f'/requirement/{req_id}/respond', data={
        'csrf_token': 'test-token',
        'proposed_fee': '1100',
        'message': 'I have 7 years experience mentoring engineering students in DSA.'
    }, follow_redirects=True)

    assert res.status_code == 200
    assert b"Your proposal has been submitted to the student" in res.data

    with app.app_context():
        proposal = RequirementResponse.query.filter_by(requirement_id=req_id, tutor_id=tutor_profile_id).first()
        assert proposal is not None
        assert proposal.proposed_fee == 1100
