from extensions import db
from models import User, TutorProfile, Subject, TuitionRequirement

DEFAULT_SUBJECTS = [
    # Academic & Core Sciences
    ("Mathematics", "Mathematics"),
    ("Calculus & Advanced Math", "Mathematics"),
    ("Statistics", "Mathematics"),
    ("Physics", "Science"),
    ("Chemistry", "Science"),
    ("Biology", "Science"),
    
    # Languages
    ("English", "Languages"),
    ("Spoken English", "Languages"),
    ("Tamil", "Languages"),
    ("Hindi", "Languages"),
    ("French", "Languages"),
    
    # Computer Science & Programming
    ("Computer Science", "Computer Science"),
    ("Python Programming", "Computer Science"),
    ("Java Programming", "Computer Science"),
    ("Web Development", "Computer Science"),
    ("Data Analytics", "Computer Science"),
    ("Machine Learning", "Computer Science"),
    
    # Commerce & Management
    ("Accounting", "Commerce"),
    ("Economics", "Commerce"),
    ("Business Studies", "Commerce"),
    
    # Competitive Exams
    ("Competitive Exam Preparation", "Exam Prep"),
    ("JEE Main & Advanced", "Exam Prep"),
    ("NEET Biology & Chemistry", "Exam Prep"),
    ("IELTS & TOEFL Prep", "Exam Prep")
]

DEMO_TUTORS = [
    {
        "full_name": "Dr. Rajesh Ramanathan",
        "email": "rajesh.maths@demo.learnbridge.com",
        "password": "Password123!",
        "city": "Chennai",
        "headline": "IIT Madras Alum & Math Educator | 12+ Years Coaching JEE & Advanced Calculus",
        "biography": "Passionate mathematics tutor with over a decade of experience helping high school and college students master complex concepts with intuitive problem-solving frameworks. Former coaching faculty with proven track record of top percentiles.",
        "qualifications": "Ph.D. in Applied Mathematics (IIT Madras), M.Sc. Mathematics",
        "experience_years": 12,
        "hourly_fee": 1200,
        "teaching_mode": "Both",
        "languages": "English, Tamil",
        "student_levels": "High School, College / University, Competitive Exams",
        "availability": "Weekday evenings & Weekend mornings",
        "subjects": ["Mathematics", "Calculus & Advanced Math", "JEE Main & Advanced", "Statistics"]
    },
    {
        "full_name": "Ananya Sharma",
        "email": "ananya.code@demo.learnbridge.com",
        "password": "Password123!",
        "city": "Bengaluru",
        "headline": "Senior Full-Stack Engineer & Python/Web Development Mentor",
        "biography": "Senior software engineer with 7+ years of experience in tech startups. I specialize in teaching Python, JavaScript, Flask, React, and Data Structures to beginners and career switchers through hands-on project building.",
        "qualifications": "B.Tech in Computer Science (NIT Surathkal), Certified Cloud Practitioner",
        "experience_years": 7,
        "hourly_fee": 1500,
        "teaching_mode": "Online",
        "languages": "English, Hindi",
        "student_levels": "High School, College / University, Working Professionals",
        "availability": "Mon-Fri 7 PM - 10 PM, Saturdays all day",
        "subjects": ["Python Programming", "Web Development", "Computer Science", "Data Analytics"]
    },
    {
        "full_name": "Prof. David Miller",
        "email": "david.english@demo.learnbridge.com",
        "password": "Password123!",
        "city": "Hyderabad",
        "headline": "Certified ESL & IELTS Specialist | Business Communication Coach",
        "biography": "Cambridge CELTA certified trainer with 9 years of teaching experience across international schools and corporate workshops. Focused on accent neutralisation, confident public speaking, and IELTS Band 8+ strategies.",
        "qualifications": "M.A. English Literature, Cambridge CELTA Certified Trainer",
        "experience_years": 9,
        "hourly_fee": 900,
        "teaching_mode": "Both",
        "languages": "English",
        "student_levels": "Middle School, High School, College, Adults / Professionals",
        "availability": "Flexible schedule (Weekdays & Weekends)",
        "subjects": ["English", "Spoken English", "IELTS & TOEFL Prep"]
    },
    {
        "full_name": "Priya Sundaram",
        "email": "priya.physics@demo.learnbridge.com",
        "password": "Password123!",
        "city": "Coimbatore",
        "headline": "Physics Faculty & NEET/CBSE Specialist | Conceptual Clarity Focus",
        "biography": "Dedicated physics educator with 6 years of experience breaking down mechanics, electromagnetism, and optics into easy visual experiments. Patient mentoring style tailored to each student's pace.",
        "qualifications": "M.Sc. Physics (Anna University), B.Ed.",
        "experience_years": 6,
        "hourly_fee": 750,
        "teaching_mode": "Both",
        "languages": "English, Tamil",
        "student_levels": "Middle School, High School, Competitive Exams",
        "availability": "Weekdays 4 PM - 8 PM",
        "subjects": ["Physics", "Science", "NEET Biology & Chemistry"]
    },
    {
        "full_name": "Arun Kumar Verma",
        "email": "arun.data@demo.learnbridge.com",
        "password": "Password123!",
        "city": "Pune",
        "headline": "Data Analytics Lead & SQL/Machine Learning Specialist",
        "biography": "Corporate analytics manager teaching practical data skills: SQL, Pandas, Tableau, and Machine Learning algorithms. 8+ years experience turning raw data into strategic insights.",
        "qualifications": "M.Tech in Data Science (BITS Pilani), B.E. Computer Engineering",
        "experience_years": 8,
        "hourly_fee": 1600,
        "teaching_mode": "Online",
        "languages": "English, Hindi",
        "student_levels": "College / University, Working Professionals",
        "availability": "Weekends 9 AM - 6 PM",
        "subjects": ["Data Analytics", "Python Programming", "Machine Learning", "Statistics"]
    },
    {
        "full_name": "Meenakshi Krishnan",
        "email": "meenakshi.commerce@demo.learnbridge.com",
        "password": "Password123!",
        "city": "Chennai",
        "headline": "Chartered Accountant & Financial Accounting Tutor",
        "biography": "Practicing CA with 10 years of experience coaching commerce students for CBSE 11-12th accounts, CA Foundation, and university level corporate finance.",
        "qualifications": "Chartered Accountant (ICAI), B.Com (Honours)",
        "experience_years": 10,
        "hourly_fee": 1100,
        "teaching_mode": "Both",
        "languages": "English, Tamil",
        "student_levels": "High School, College / University, Professional Exams",
        "availability": "Tues, Thurs, Sat 5 PM - 9 PM",
        "subjects": ["Accounting", "Economics", "Business Studies"]
    },
    {
        "full_name": "Siddharth Sen",
        "email": "siddharth.java@demo.learnbridge.com",
        "password": "Password123!",
        "city": "Mumbai",
        "headline": "Java Backend Architect & DSA Instructor for Tech Interviews",
        "biography": "Senior systems engineer at an investment bank. I coach students and aspiring software engineers in core Java, Object-Oriented Design, Spring Boot, and LeetCode algorithmic problem solving.",
        "qualifications": "B.Tech Computer Science (VJTI Mumbai)",
        "experience_years": 5,
        "hourly_fee": 1400,
        "teaching_mode": "Online",
        "languages": "English, Hindi",
        "student_levels": "College / University, Working Professionals",
        "availability": "Weekday mornings 7 AM - 9 AM, Sundays all day",
        "subjects": ["Java Programming", "Computer Science", "Web Development"]
    },
    {
        "full_name": "Kavitha Balakrishnan",
        "email": "kavitha.tamil@demo.learnbridge.com",
        "password": "Password123!",
        "city": "Madurai",
        "headline": "Tamil Language Scholar & Literature Tutor | All Age Groups",
        "biography": "Passionate Tamil teacher with 14 years of teaching experience in schools and community centers. Specializing in spoken Tamil for beginners, classical literature, and state board curriculum.",
        "qualifications": "M.A. Tamil Literature, M.Phil, B.Ed.",
        "experience_years": 14,
        "hourly_fee": 600,
        "teaching_mode": "Both",
        "languages": "Tamil, English",
        "student_levels": "Primary School, Middle School, High School, Adults",
        "availability": "Monday to Saturday 3 PM - 7 PM",
        "subjects": ["Tamil", "Languages"]
    }
]

DEMO_STUDENTS = [
    {
        "full_name": "Karthik Narayanan",
        "email": "karthik.student@demo.learnbridge.com",
        "password": "Password123!",
        "city": "Chennai",
        "requirements": [
            {
                "subject_name": "Mathematics",
                "student_level": "Grade 12 / Higher Secondary",
                "teaching_mode": "Online",
                "location": "Chennai",
                "budget": 1000,
                "preferred_schedule": "3 days a week, evenings after 6 PM",
                "description": "Looking for an experienced tutor for Class 12 CBSE calculus and vectors. Need help preparing for board exams and solving past 5 years question papers."
            }
        ]
    },
    {
        "full_name": "Sneha Roy",
        "email": "sneha.student@demo.learnbridge.com",
        "password": "Password123!",
        "city": "Bengaluru",
        "requirements": [
            {
                "subject_name": "Python Programming",
                "student_level": "College / University",
                "teaching_mode": "Online",
                "location": "Bengaluru",
                "budget": 1200,
                "preferred_schedule": "Weekends 10 AM - 12 PM",
                "description": "First-year engineering student needing structured guidance with Python programming, OOP concepts, and mini-project implementation."
            }
        ]
    }
]

def apply_schema_migrations():
    """Ensure newly added columns exist in the database without dropping tables."""
    queries = [
        "ALTER TABLE tutor_profiles ADD COLUMN IF NOT EXISTS upi_id VARCHAR(100)",
        "ALTER TABLE tutor_profiles ADD COLUMN IF NOT EXISTS payment_instructions TEXT",
        "ALTER TABLE tuition_requests ADD COLUMN IF NOT EXISTS payment_status VARCHAR(20) DEFAULT 'unpaid'",
        "ALTER TABLE tuition_requests ADD COLUMN IF NOT EXISTS payment_reference VARCHAR(100)",
        "ALTER TABLE tuition_requests ADD COLUMN IF NOT EXISTS payment_notes TEXT",
        "ALTER TABLE tuition_requests ADD COLUMN IF NOT EXISTS paid_at TIMESTAMP",
    ]
    for q in queries:
        try:
            db.session.execute(db.text(q))
            db.session.commit()
        except Exception:
            db.session.rollback()

def seed_database():
    """Populates subjects, sample tutors, and sample requirements if not present."""
    apply_schema_migrations()

    # 1. Seed Subjects
    subject_map = {}
    for name, category in DEFAULT_SUBJECTS:
        subject = Subject.query.filter_by(name=name).first()
        if not subject:
            subject = Subject(name=name, category=category)
            db.session.add(subject)
            db.session.flush()
        subject_map[name] = subject

    db.session.commit()

    # 2. Seed Demo Tutors
    for t_data in DEMO_TUTORS:
        user = User.query.filter_by(email=t_data["email"]).first()
        if not user:
            user = User(
                full_name=t_data["full_name"],
                email=t_data["email"],
                role="tutor",
                city=t_data["city"]
            )
            user.set_password(t_data["password"])
            db.session.add(user)
            db.session.flush()

            profile = TutorProfile(
                user_id=user.id,
                headline=t_data["headline"],
                biography=t_data["biography"],
                qualifications=t_data["qualifications"],
                experience_years=t_data["experience_years"],
                hourly_fee=t_data["hourly_fee"],
                teaching_mode=t_data["teaching_mode"],
                languages=t_data["languages"],
                student_levels=t_data["student_levels"],
                availability=t_data["availability"]
            )
            for s_name in t_data["subjects"]:
                if s_name in subject_map:
                    profile.subjects.append(subject_map[s_name])
            db.session.add(profile)
        elif user and user.tutor_profile and not user.tutor_profile.upi_id:
            clean_name = user.full_name.lower().replace("dr. ", "").replace("prof. ", "").replace(" ", ".")
            user.tutor_profile.upi_id = f"{clean_name}@okaxis"
            user.tutor_profile.payment_instructions = "Pay via GPay, PhonePe, or Paytm UPI, then submit your transaction UTR reference below."

    db.session.commit()

    # 3. Seed Demo Students and Tuition Requirements
    for s_data in DEMO_STUDENTS:
        student = User.query.filter_by(email=s_data["email"]).first()
        if not student:
            student = User(
                full_name=s_data["full_name"],
                email=s_data["email"],
                role="student",
                city=s_data["city"]
            )
            student.set_password(s_data["password"])
            db.session.add(student)
            db.session.flush()

            for req in s_data["requirements"]:
                subj = subject_map.get(req["subject_name"])
                tuition_req = TuitionRequirement(
                    student_id=student.id,
                    subject_id=subj.id if subj else None,
                    student_level=req["student_level"],
                    teaching_mode=req["teaching_mode"],
                    location=req["location"],
                    budget=req["budget"],
                    preferred_schedule=req["preferred_schedule"],
                    description=req["description"],
                    status="open"
                )
                db.session.add(tuition_req)

    db.session.commit()
    print("Database seeding completed successfully.")

if __name__ == '__main__':
    from flask import Flask
    from config import Config

    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    with app.app_context():
        db.create_all()
        seed_database()
