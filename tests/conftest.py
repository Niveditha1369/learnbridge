import pytest
from app import create_app
from extensions import db
from models import User, TutorProfile, Subject, TuitionRequest, TuitionRequirement
from seed import DEFAULT_SUBJECTS


class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'test-secret-key-12345'
    WTF_CSRF_ENABLED = False


@pytest.fixture
def app():
    app = create_app(TestConfig)

    with app.app_context():
        db.create_all()
        # Seed test subjects
        for name, category in DEFAULT_SUBJECTS[:6]:
            s = Subject(name=name, category=category)
            db.session.add(s)
        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def sample_tutor(app):
    with app.app_context():
        user = User(
            full_name="Prof. Sharma",
            email="prof.sharma@example.com",
            role="tutor",
            city="Chennai"
        )
        user.set_password("SecurePassword123!")
        db.session.add(user)
        db.session.flush()

        profile = TutorProfile(
            user_id=user.id,
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
            profile.subjects.append(math_subj)
        db.session.add(profile)
        db.session.commit()
        return user.id, profile.id


@pytest.fixture
def sample_student(app):
    with app.app_context():
        user = User(
            full_name="Kavya Student",
            email="kavya@example.com",
            role="student",
            city="Chennai"
        )
        user.set_password("StudentPassword123!")
        db.session.add(user)
        db.session.commit()
        return user.id
