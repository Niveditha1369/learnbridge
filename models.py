from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db

# Association Table for Tutor-Subject Many-to-Many
tutor_subjects = db.Table(
    'tutor_subjects',
    db.Column('tutor_id', db.Integer, db.ForeignKey('tutor_profiles.id', ondelete='CASCADE'), primary_key=True),
    db.Column('subject_id', db.Integer, db.ForeignKey('subjects.id', ondelete='CASCADE'), primary_key=True)
)


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'student' or 'tutor'
    city = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    tutor_profile = db.relationship('TutorProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    sent_requests = db.relationship('TuitionRequest', backref='student', lazy='dynamic', cascade='all, delete-orphan', foreign_keys='TuitionRequest.student_id')
    posted_requirements = db.relationship('TuitionRequirement', backref='student', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'full_name': self.full_name,
            'email': self.email,
            'role': self.role,
            'city': self.city,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class TutorProfile(db.Model):
    __tablename__ = 'tutor_profiles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    headline = db.Column(db.String(200), nullable=False)
    biography = db.Column(db.Text, nullable=False)
    qualifications = db.Column(db.Text, nullable=False)
    experience_years = db.Column(db.Integer, nullable=False, default=1)
    hourly_fee = db.Column(db.Integer, nullable=False)  # In INR
    teaching_mode = db.Column(db.String(50), nullable=False, default='Both')  # 'Online', 'In-Person', 'Both'
    languages = db.Column(db.String(200), nullable=False, default='English')
    student_levels = db.Column(db.String(200), nullable=False, default='Middle School, High School')
    availability = db.Column(db.String(200), nullable=False, default='Weekdays, Flexible')
    profile_image_path = db.Column(db.String(255), nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    subjects = db.relationship('Subject', secondary=tutor_subjects, backref=db.backref('tutors', lazy='dynamic'))
    received_requests = db.relationship('TuitionRequest', backref='tutor_profile', lazy='dynamic', cascade='all, delete-orphan', foreign_keys='TuitionRequest.tutor_id')
    responses = db.relationship('RequirementResponse', backref='tutor_profile', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self, include_user=True):
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'headline': self.headline,
            'biography': self.biography,
            'qualifications': self.qualifications,
            'experience_years': self.experience_years,
            'hourly_fee': self.hourly_fee,
            'teaching_mode': self.teaching_mode,
            'languages': self.languages,
            'student_levels': self.student_levels,
            'availability': self.availability,
            'profile_image_path': self.profile_image_path,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'subjects': [s.to_dict() for s in self.subjects]
        }
        if include_user and self.user:
            data['full_name'] = self.user.full_name
            data['city'] = self.user.city
        return data


class Subject(db.Model):
    __tablename__ = 'subjects'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    category = db.Column(db.String(100), nullable=False, index=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category
        }


class TuitionRequest(db.Model):
    __tablename__ = 'tuition_requests'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    tutor_id = db.Column(db.Integer, db.ForeignKey('tutor_profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id', ondelete='SET NULL'), nullable=True)
    student_level = db.Column(db.String(50), nullable=False)
    teaching_mode = db.Column(db.String(50), nullable=False)
    preferred_schedule = db.Column(db.String(100), nullable=False)
    budget = db.Column(db.Integer, nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='pending', nullable=False)  # pending, accepted, rejected, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    subject = db.relationship('Subject', backref='tuition_requests')

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.full_name if self.student else None,
            'student_city': self.student.city if self.student else None,
            'tutor_id': self.tutor_id,
            'tutor_name': self.tutor_profile.user.full_name if (self.tutor_profile and self.tutor_profile.user) else None,
            'subject_id': self.subject_id,
            'subject_name': self.subject.name if self.subject else 'General Tuition',
            'student_level': self.student_level,
            'teaching_mode': self.teaching_mode,
            'preferred_schedule': self.preferred_schedule,
            'budget': self.budget,
            'message': self.message,
            'status': self.status,
            'created_at': self.created_at.strftime('%b %d, %Y %I:%M %p') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%b %d, %Y %I:%M %p') if self.updated_at else None
        }


class TuitionRequirement(db.Model):
    __tablename__ = 'tuition_requirements'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id', ondelete='SET NULL'), nullable=True)
    student_level = db.Column(db.String(50), nullable=False)
    teaching_mode = db.Column(db.String(50), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    budget = db.Column(db.Integer, nullable=False)
    preferred_schedule = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='open', nullable=False)  # open, fulfilled, closed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    subject = db.relationship('Subject', backref='tuition_requirements')
    responses = db.relationship('RequirementResponse', backref='requirement', lazy='dynamic', cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'student_name': self.student.full_name if self.student else 'Anonymous Student',
            'subject_id': self.subject_id,
            'subject_name': self.subject.name if self.subject else 'General',
            'student_level': self.student_level,
            'teaching_mode': self.teaching_mode,
            'location': self.location,
            'budget': self.budget,
            'preferred_schedule': self.preferred_schedule,
            'description': self.description,
            'status': self.status,
            'response_count': self.responses.count(),
            'created_at': self.created_at.strftime('%b %d, %Y') if self.created_at else None
        }


class RequirementResponse(db.Model):
    __tablename__ = 'requirement_responses'

    id = db.Column(db.Integer, primary_key=True)
    requirement_id = db.Column(db.Integer, db.ForeignKey('tuition_requirements.id', ondelete='CASCADE'), nullable=False, index=True)
    tutor_id = db.Column(db.Integer, db.ForeignKey('tutor_profiles.id', ondelete='CASCADE'), nullable=False, index=True)
    message = db.Column(db.Text, nullable=False)
    proposed_fee = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'requirement_id': self.requirement_id,
            'tutor_id': self.tutor_id,
            'tutor_name': self.tutor_profile.user.full_name if (self.tutor_profile and self.tutor_profile.user) else 'Tutor',
            'tutor_headline': self.tutor_profile.headline if self.tutor_profile else '',
            'message': self.message,
            'proposed_fee': self.proposed_fee,
            'created_at': self.created_at.strftime('%b %d, %Y') if self.created_at else None
        }
