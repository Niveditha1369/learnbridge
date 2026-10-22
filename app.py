import os
import asyncio
if not hasattr(asyncio, 'Runner'):
    asyncio.Runner = object

import secrets
from functools import wraps
from datetime import datetime
from flask import (
    Flask, render_template, request, redirect, url_for,
    flash, session, jsonify, abort
)
from sqlalchemy import or_, and_, desc, asc

from config import Config
from extensions import db
from models import (
    User, TutorProfile, Subject, TuitionRequest,
    TuitionRequirement, RequirementResponse, tutor_subjects
)
from seed import seed_database


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)

    # Ensure upload directory exists
    os.makedirs(app.config.get('UPLOAD_FOLDER', 'static/uploads'), exist_ok=True)

    # --- CSRF & Auth Helpers ---
    @app.before_request
    def set_csrf_token():
        if 'csrf_token' not in session:
            session['csrf_token'] = secrets.token_hex(32)

    @app.context_processor
    def inject_global_data():
        current_user = None
        user_id = session.get('user_id')
        if user_id:
            current_user = db.session.get(User, user_id)
        return {
            'current_user': current_user,
            'csrf_token': session.get('csrf_token', ''),
            'now': datetime.utcnow()
        }

    def verify_csrf():
        token = request.form.get('csrf_token') or request.headers.get('X-CSRF-Token')
        session_token = session.get('csrf_token')
        if not session_token or not token or not secrets.compare_digest(token, session_token):
            abort(400, description="Invalid or missing CSRF token.")

    def login_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                if request.is_json:
                    return jsonify({'error': 'Authentication required'}), 401
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('login', next=request.url))
            return f(*args, **kwargs)
        return decorated_function

    def role_required(role):
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if 'user_id' not in session:
                    if request.is_json:
                        return jsonify({'error': 'Authentication required'}), 401
                    flash('Please log in to continue.', 'warning')
                    return redirect(url_for('login'))
                user = db.session.get(User, session['user_id'])
                if not user or user.role != role:
                    if request.is_json:
                        return jsonify({'error': f'Unauthorized. {role.capitalize()} access only.'}), 403
                    flash(f'Access restricted to {role}s only.', 'danger')
                    return redirect(url_for('index'))
                return f(*args, **kwargs)
            return decorated_function
        return decorator

    # --- CLI & Initializer Commands ---
    @app.cli.command('init-db')
    def init_db():
        """Initialize schema and seed demo data."""
        db.create_all()
        seed_database()
        print("Database initialized and seeded.")

    # --- Health Check Endpoint (For Render) ---
    @app.route('/healthz')
    def health_check():
        try:
            # Verify DB connectivity
            db.session.execute(db.text('SELECT 1'))
            return jsonify({'status': 'healthy', 'database': 'connected'}), 200
        except Exception as e:
            return jsonify({'status': 'unhealthy', 'error': str(e)}), 500

    # ==========================================
    # 1. HOMEPAGE & CORE STATIC ROUTES
    # ==========================================
    @app.route('/')
    def index():
        featured_tutors = TutorProfile.query.join(User).order_by(TutorProfile.experience_years.desc()).limit(6).all()
        popular_subjects = Subject.query.order_by(Subject.name).limit(14).all()
        total_tutors = TutorProfile.query.count()
        total_students = User.query.filter_by(role='student').count()
        total_subjects = Subject.query.count()
        return render_template(
            'index.html',
            featured_tutors=featured_tutors,
            popular_subjects=popular_subjects,
            stats={
                'tutors': total_tutors,
                'students': total_students,
                'subjects': total_subjects
            }
        )

    @app.route('/about')
    def about():
        return render_template('about.html')

    @app.route('/contact', methods=['GET', 'POST'])
    def contact():
        if request.method == 'POST':
            verify_csrf()
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            message = request.form.get('message', '').strip()
            if not name or not email or not message:
                flash('Please fill in all required fields.', 'danger')
            else:
                flash('Thank you for contacting LearnBridge. Our support team will get back to you shortly.', 'success')
                return redirect(url_for('contact'))
        return render_template('contact.html')

    @app.route('/privacy')
    def privacy():
        return render_template('privacy.html')

    @app.route('/terms')
    def terms():
        return render_template('terms.html')

    # ==========================================
    # 2. AUTHENTICATION (STUDENT & TUTOR)
    # ==========================================
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if 'user_id' in session:
            return redirect(url_for('index'))

        if request.method == 'POST':
            verify_csrf()
            full_name = request.form.get('full_name', '').strip()
            email = request.form.get('email', '').strip().lower()
            city = request.form.get('city', '').strip()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')

            # Validation
            if not full_name or not email or not city or not password:
                flash('All fields are required.', 'danger')
                return render_template('register.html', full_name=full_name, email=email, city=city)

            if len(password) < 6:
                flash('Password must be at least 6 characters long.', 'danger')
                return render_template('register.html', full_name=full_name, email=email, city=city)

            if password != confirm_password:
                flash('Passwords do not match.', 'danger')
                return render_template('register.html', full_name=full_name, email=email, city=city)

            if User.query.filter_by(email=email).first():
                flash('An account with this email address already exists. Please log in.', 'warning')
                return render_template('register.html', full_name=full_name, email=email, city=city)

            user = User(
                full_name=full_name,
                email=email,
                city=city,
                role='student'
            )
            user.set_password(password)
            db.session.add(user)
            db.session.commit()

            session['user_id'] = user.id
            session['user_role'] = user.role
            session['user_name'] = user.full_name
            flash(f'Welcome to LearnBridge, {user.full_name}! Your student account has been created.', 'success')
            return redirect(url_for('student_dashboard'))

        return render_template('register.html')

    @app.route('/become-tutor', methods=['GET', 'POST'])
    def become_tutor():
        if 'user_id' in session:
            user = db.session.get(User, session['user_id'])
            if user and user.role == 'tutor':
                return redirect(url_for('tutor_dashboard'))

        subjects = Subject.query.order_by(Subject.name).all()

        if request.method == 'POST':
            verify_csrf()
            full_name = request.form.get('full_name', '').strip()
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            city = request.form.get('city', '').strip()
            headline = request.form.get('headline', '').strip()
            biography = request.form.get('biography', '').strip()
            qualifications = request.form.get('qualifications', '').strip()
            experience_years = request.form.get('experience_years', '0').strip()
            hourly_fee = request.form.get('hourly_fee', '0').strip()
            teaching_mode = request.form.get('teaching_mode', 'Both').strip()
            languages = request.form.get('languages', 'English').strip()
            student_levels = request.form.get('student_levels', 'High School').strip()
            availability = request.form.get('availability', 'Flexible').strip()
            selected_subject_ids = request.form.getlist('subjects')

            # Validation
            if not full_name or not email or not password or not city or not headline or not biography:
                flash('Please fill in all mandatory fields.', 'danger')
                return render_template('become_tutor.html', subjects=subjects)

            if len(password) < 6:
                flash('Password must be at least 6 characters long.', 'danger')
                return render_template('become_tutor.html', subjects=subjects)

            if password != confirm_password:
                flash('Passwords do not match.', 'danger')
                return render_template('become_tutor.html', subjects=subjects)

            if User.query.filter_by(email=email).first():
                flash('An account with this email address already exists. Please log in.', 'warning')
                return render_template('become_tutor.html', subjects=subjects)

            try:
                exp_int = int(experience_years)
                fee_int = int(hourly_fee)
            except ValueError:
                flash('Experience and Hourly Fee must be valid numbers.', 'danger')
                return render_template('become_tutor.html', subjects=subjects)

            # Create User
            user = User(
                full_name=full_name,
                email=email,
                city=city,
                role='tutor'
            )
            user.set_password(password)
            db.session.add(user)
            db.session.flush()

            # Create Tutor Profile
            profile = TutorProfile(
                user_id=user.id,
                headline=headline,
                biography=biography,
                qualifications=qualifications,
                experience_years=exp_int,
                hourly_fee=fee_int,
                teaching_mode=teaching_mode,
                languages=languages,
                student_levels=student_levels,
                availability=availability
            )

            # Attach selected subjects
            for sid in selected_subject_ids:
                subj = db.session.get(Subject, int(sid))
                if subj:
                    profile.subjects.append(subj)

            db.session.add(profile)
            db.session.commit()

            session['user_id'] = user.id
            session['user_role'] = user.role
            session['user_name'] = user.full_name
            flash(f'Welcome to LearnBridge, {user.full_name}! Your tutor profile has been registered.', 'success')
            return redirect(url_for('tutor_dashboard'))

        return render_template('become_tutor.html', subjects=subjects)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if 'user_id' in session:
            role = session.get('user_role')
            if role == 'tutor':
                return redirect(url_for('tutor_dashboard'))
            return redirect(url_for('student_dashboard'))

        if request.method == 'POST':
            verify_csrf()
            email = request.form.get('email', '').strip().lower()
            password = request.form.get('password', '')

            user = User.query.filter_by(email=email).first()
            if not user or not user.check_password(password):
                flash('Invalid email or password. Please try again.', 'danger')
                return render_template('login.html', email=email)

            session['user_id'] = user.id
            session['user_role'] = user.role
            session['user_name'] = user.full_name

            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)

            flash(f'Welcome back, {user.full_name}!', 'success')
            if user.role == 'tutor':
                return redirect(url_for('tutor_dashboard'))
            return redirect(url_for('student_dashboard'))

        return render_template('login.html')

    @app.route('/logout', methods=['GET', 'POST'])
    def logout():
        session.clear()
        flash('You have been logged out successfully.', 'info')
        return redirect(url_for('index'))

    # ==========================================
    # 3. TUTOR DIRECTORY & PROFILE
    # ==========================================
    @app.route('/tutors')
    def tutors():
        subject_param = request.args.get('subject', '').strip()
        q = request.args.get('q', '').strip()
        city = request.args.get('city', '').strip()
        teaching_mode = request.args.get('teaching_mode', '').strip()
        min_fee = request.args.get('min_fee', '').strip()
        max_fee = request.args.get('max_fee', '').strip()
        min_exp = request.args.get('min_exp', '').strip()
        language = request.args.get('language', '').strip()
        student_level = request.args.get('student_level', '').strip()
        sort_by = request.args.get('sort_by', 'exp_desc').strip()
        page = request.args.get('page', 1, type=int)

        query = TutorProfile.query.join(User)

        # Filters
        if q:
            search_term = f"%{q}%"
            query = query.filter(
                or_(
                    User.full_name.ilike(search_term),
                    TutorProfile.headline.ilike(search_term),
                    TutorProfile.biography.ilike(search_term)
                )
            )

        if subject_param:
            # Check by subject ID or name
            if subject_param.isdigit():
                query = query.filter(TutorProfile.subjects.any(Subject.id == int(subject_param)))
            else:
                query = query.filter(TutorProfile.subjects.any(Subject.name.ilike(f"%{subject_param}%")))

        if city:
            query = query.filter(User.city.ilike(f"%{city}%"))

        if teaching_mode and teaching_mode != 'Any':
            if teaching_mode == 'Both':
                query = query.filter(TutorProfile.teaching_mode == 'Both')
            else:
                query = query.filter(or_(TutorProfile.teaching_mode == teaching_mode, TutorProfile.teaching_mode == 'Both'))

        if min_fee.isdigit():
            query = query.filter(TutorProfile.hourly_fee >= int(min_fee))

        if max_fee.isdigit():
            query = query.filter(TutorProfile.hourly_fee <= int(max_fee))

        if min_exp.isdigit():
            query = query.filter(TutorProfile.experience_years >= int(min_exp))

        if language:
            query = query.filter(TutorProfile.languages.ilike(f"%{language}%"))

        if student_level:
            query = query.filter(TutorProfile.student_levels.ilike(f"%{student_level}%"))

        # Sorting
        if sort_by == 'fee_asc':
            query = query.order_by(asc(TutorProfile.hourly_fee))
        elif sort_by == 'fee_desc':
            query = query.order_by(desc(TutorProfile.hourly_fee))
        elif sort_by == 'exp_desc':
            query = query.order_by(desc(TutorProfile.experience_years))
        else:
            query = query.order_by(desc(TutorProfile.updated_at))

        per_page = 9
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        all_subjects = Subject.query.order_by(Subject.name).all()

        return render_template(
            'tutors.html',
            pagination=pagination,
            tutors=pagination.items,
            all_subjects=all_subjects,
            selected_subject=subject_param,
            current_filters={
                'q': q,
                'subject': subject_param,
                'city': city,
                'teaching_mode': teaching_mode,
                'min_fee': min_fee,
                'max_fee': max_fee,
                'min_exp': min_exp,
                'language': language,
                'student_level': student_level,
                'sort_by': sort_by
            }
        )

    @app.route('/tutor/<int:tutor_id>')
    def tutor_profile(tutor_id):
        profile = db.session.get(TutorProfile, tutor_id)
        if not profile:
            flash('Tutor profile not found.', 'danger')
            return redirect(url_for('tutors'))
        
        # User details safe display (no email/password)
        return render_template('tutor_profile.html', profile=profile)

    # ==========================================
    # 4. TUITION REQUEST WORKFLOW
    # ==========================================
    @app.route('/tutor/<int:tutor_id>/request', methods=['POST'])
    @login_required
    def send_tuition_request(tutor_id):
        verify_csrf()
        user = db.session.get(User, session['user_id'])
        if user.role != 'student':
            flash('Only students can send tuition requests.', 'danger')
            return redirect(url_for('tutor_profile', tutor_id=tutor_id))

        profile = db.session.get(TutorProfile, tutor_id)
        if not profile:
            flash('Tutor not found.', 'danger')
            return redirect(url_for('tutors'))

        subject_id = request.form.get('subject_id')
        student_level = request.form.get('student_level', '').strip()
        teaching_mode = request.form.get('teaching_mode', 'Online').strip()
        preferred_schedule = request.form.get('preferred_schedule', '').strip()
        budget = request.form.get('budget', str(profile.hourly_fee)).strip()
        message = request.form.get('message', '').strip()

        if not student_level or not preferred_schedule or not message:
            flash('Please complete all required fields in the request.', 'danger')
            return redirect(url_for('tutor_profile', tutor_id=tutor_id))

        try:
            budget_int = int(budget)
        except ValueError:
            budget_int = profile.hourly_fee

        subj_obj = db.session.get(Subject, int(subject_id)) if subject_id and subject_id.isdigit() else None

        req = TuitionRequest(
            student_id=user.id,
            tutor_id=profile.id,
            subject_id=subj_obj.id if subj_obj else None,
            student_level=student_level,
            teaching_mode=teaching_mode,
            preferred_schedule=preferred_schedule,
            budget=budget_int,
            message=message,
            status='pending'
        )
        db.session.add(req)
        db.session.commit()

        flash(f'Your tuition enquiry has been sent to {profile.user.full_name}! Track its status in your dashboard.', 'success')
        return redirect(url_for('student_dashboard'))

    # ==========================================
    # 5. FIND TUITION / POST REQUIREMENT BOARD
    # ==========================================
    @app.route('/find-tuition', methods=['GET', 'POST'])
    def find_tuition():
        subjects = Subject.query.order_by(Subject.name).all()

        if request.method == 'POST':
            verify_csrf()
            if 'user_id' not in session:
                flash('Please log in as a student to post a tuition requirement.', 'warning')
                return redirect(url_for('login', next=url_for('find_tuition')))

            user = db.session.get(User, session['user_id'])
            if user.role != 'student':
                flash('Only student accounts can post tuition requirements.', 'danger')
                return redirect(url_for('find_tuition'))

            subject_id = request.form.get('subject_id')
            student_level = request.form.get('student_level', '').strip()
            teaching_mode = request.form.get('teaching_mode', 'Online').strip()
            location = request.form.get('location', user.city).strip()
            budget = request.form.get('budget', '500').strip()
            preferred_schedule = request.form.get('preferred_schedule', '').strip()
            description = request.form.get('description', '').strip()

            if not student_level or not preferred_schedule or not description or not location:
                flash('Please fill in all required requirement fields.', 'danger')
                return redirect(url_for('find_tuition'))

            try:
                budget_int = int(budget)
            except ValueError:
                budget_int = 500

            subj_obj = db.session.get(Subject, int(subject_id)) if subject_id and subject_id.isdigit() else None

            tuition_req = TuitionRequirement(
                student_id=user.id,
                subject_id=subj_obj.id if subj_obj else None,
                student_level=student_level,
                teaching_mode=teaching_mode,
                location=location,
                budget=budget_int,
                preferred_schedule=preferred_schedule,
                description=description,
                status='open'
            )
            db.session.add(tuition_req)
            db.session.commit()

            flash('Your tuition requirement has been posted successfully! Tutors can now view and respond to it.', 'success')
            return redirect(url_for('student_dashboard'))

        # Filters for viewing requirements
        subject_filter = request.args.get('subject', '').strip()
        location_filter = request.args.get('location', '').strip()
        mode_filter = request.args.get('mode', '').strip()
        page = request.args.get('page', 1, type=int)

        query = TuitionRequirement.query.filter_by(status='open').order_by(TuitionRequirement.created_at.desc())

        if subject_filter:
            if subject_filter.isdigit():
                query = query.filter_by(subject_id=int(subject_filter))
            else:
                query = query.join(Subject).filter(Subject.name.ilike(f"%{subject_filter}%"))

        if location_filter:
            query = query.filter(TuitionRequirement.location.ilike(f"%{location_filter}%"))

        if mode_filter and mode_filter != 'Any':
            query = query.filter(TuitionRequirement.teaching_mode == mode_filter)

        pagination = query.paginate(page=page, per_page=10, error_out=False)

        return render_template(
            'find_tuition.html',
            pagination=pagination,
            requirements=pagination.items,
            subjects=subjects,
            selected_subject=subject_filter,
            selected_location=location_filter,
            selected_mode=mode_filter
        )

    @app.route('/requirement/<int:req_id>/respond', methods=['POST'])
    @role_required('tutor')
    def respond_to_requirement(req_id):
        verify_csrf()
        user = db.session.get(User, session['user_id'])
        profile = user.tutor_profile
        if not profile:
            flash('Tutor profile missing.', 'danger')
            return redirect(url_for('tutor_dashboard'))

        requirement = db.session.get(TuitionRequirement, req_id)
        if not requirement or requirement.status != 'open':
            flash('This requirement is no longer accepting responses.', 'danger')
            return redirect(url_for('find_tuition'))

        message = request.form.get('message', '').strip()
        proposed_fee = request.form.get('proposed_fee', str(profile.hourly_fee)).strip()

        if not message:
            flash('Please write a message explaining your experience and offer.', 'danger')
            return redirect(url_for('find_tuition'))

        try:
            fee_int = int(proposed_fee)
        except ValueError:
            fee_int = profile.hourly_fee

        response_entry = RequirementResponse(
            requirement_id=requirement.id,
            tutor_id=profile.id,
            message=message,
            proposed_fee=fee_int
        )
        db.session.add(response_entry)
        db.session.commit()

        flash('Your proposal has been submitted to the student!', 'success')
        return redirect(url_for('find_tuition'))

    # ==========================================
    # 6. STUDENT DASHBOARD & ACTIONS
    # ==========================================
    @app.route('/student/dashboard')
    @role_required('student')
    def student_dashboard():
        user = db.session.get(User, session['user_id'])
        requests = TuitionRequest.query.filter_by(student_id=user.id).order_by(TuitionRequest.created_at.desc()).all()
        requirements = TuitionRequirement.query.filter_by(student_id=user.id).order_by(TuitionRequirement.created_at.desc()).all()

        stats = {
            'total': len(requests),
            'pending': sum(1 for r in requests if r.status == 'pending'),
            'accepted': sum(1 for r in requests if r.status == 'accepted'),
            'rejected': sum(1 for r in requests if r.status == 'rejected')
        }

        subjects = Subject.query.order_by(Subject.name).all()

        return render_template(
            'student_dashboard.html',
            user=user,
            requests=requests,
            requirements=requirements,
            stats=stats,
            subjects=subjects
        )

    @app.route('/student/request/<int:req_id>/cancel', methods=['POST'])
    @role_required('student')
    def cancel_student_request(req_id):
        verify_csrf()
        user_id = session['user_id']
        req = db.session.get(TuitionRequest, req_id)

        if not req or req.student_id != user_id:
            flash('Request not found or unauthorized.', 'danger')
            return redirect(url_for('student_dashboard'))

        if req.status != 'pending':
            flash('Only pending requests can be cancelled.', 'warning')
            return redirect(url_for('student_dashboard'))

        req.status = 'cancelled'
        db.session.commit()
        flash('Tuition request has been cancelled.', 'info')
        return redirect(url_for('student_dashboard'))

    @app.route('/student/requirement/<int:req_id>/close', methods=['POST'])
    @role_required('student')
    def close_student_requirement(req_id):
        verify_csrf()
        user_id = session['user_id']
        req = db.session.get(TuitionRequirement, req_id)

        if not req or req.student_id != user_id:
            flash('Requirement not found or unauthorized.', 'danger')
            return redirect(url_for('student_dashboard'))

        req.status = 'closed'
        db.session.commit()
        flash('Tuition requirement marked as closed.', 'info')
        return redirect(url_for('student_dashboard'))

    @app.route('/student/profile/update', methods=['POST'])
    @role_required('student')
    def update_student_profile():
        verify_csrf()
        user = db.session.get(User, session['user_id'])
        full_name = request.form.get('full_name', '').strip()
        city = request.form.get('city', '').strip()

        if full_name and city:
            user.full_name = full_name
            user.city = city
            session['user_name'] = full_name
            db.session.commit()
            flash('Profile updated successfully.', 'success')
        else:
            flash('Full name and city cannot be empty.', 'danger')

        return redirect(url_for('student_dashboard'))

    @app.route('/student/request/<int:req_id>/pay', methods=['POST'])
    @role_required('student')
    def student_submit_payment(req_id):
        verify_csrf()
        user_id = session['user_id']
        req = db.session.get(TuitionRequest, req_id)

        if not req or req.student_id != user_id:
            flash('Request not found or unauthorized.', 'danger')
            return redirect(url_for('student_dashboard'))

        if req.status != 'accepted':
            flash('Payment can only be submitted for accepted requests.', 'warning')
            return redirect(url_for('student_dashboard'))

        payment_reference = request.form.get('payment_reference', '').strip()
        payment_notes = request.form.get('payment_notes', '').strip()

        if not payment_reference:
            flash('Please enter your payment reference / UTR transaction ID.', 'danger')
            return redirect(url_for('student_dashboard'))

        req.payment_status = 'paid_submitted'
        req.payment_reference = payment_reference
        req.payment_notes = payment_notes
        req.paid_at = datetime.utcnow()
        db.session.commit()

        flash('Payment details submitted! Your tutor will verify and confirm.', 'success')
        return redirect(url_for('student_dashboard'))

    # ==========================================
    # 7. TUTOR DASHBOARD & ACTIONS
    # ==========================================
    @app.route('/tutor/dashboard')
    @role_required('tutor')
    def tutor_dashboard():
        user = db.session.get(User, session['user_id'])
        profile = user.tutor_profile
        if not profile:
            flash('Tutor profile not found. Please contact support.', 'danger')
            return redirect(url_for('index'))

        incoming_requests = TuitionRequest.query.filter_by(tutor_id=profile.id).order_by(TuitionRequest.created_at.desc()).all()
        all_subjects = Subject.query.order_by(Subject.name).all()

        stats = {
            'total': len(incoming_requests),
            'pending': sum(1 for r in incoming_requests if r.status == 'pending'),
            'accepted': sum(1 for r in incoming_requests if r.status == 'accepted'),
            'rejected': sum(1 for r in incoming_requests if r.status == 'rejected')
        }

        # Calculate completion percentage
        completion_fields = [
            profile.headline, profile.biography, profile.qualifications,
            profile.experience_years, profile.hourly_fee, profile.teaching_mode,
            profile.languages, profile.student_levels, profile.availability,
            len(profile.subjects) > 0
        ]
        completion_score = int((sum(1 for f in completion_fields if f) / len(completion_fields)) * 100)

        # Recent open requirements for browsing
        open_requirements = TuitionRequirement.query.filter_by(status='open').order_by(TuitionRequirement.created_at.desc()).limit(5).all()

        return render_template(
            'tutor_dashboard.html',
            user=user,
            profile=profile,
            requests=incoming_requests,
            stats=stats,
            completion_score=completion_score,
            all_subjects=all_subjects,
            open_requirements=open_requirements
        )

    @app.route('/tutor/request/<int:req_id>/status', methods=['POST'])
    @role_required('tutor')
    def update_tutor_request_status(req_id):
        verify_csrf()
        user = db.session.get(User, session['user_id'])
        profile = user.tutor_profile
        req = db.session.get(TuitionRequest, req_id)

        if not req or req.tutor_id != profile.id:
            flash('Request not found or unauthorized.', 'danger')
            return redirect(url_for('tutor_dashboard'))

        new_status = request.form.get('status', '').strip().lower()
        if new_status not in ['accepted', 'rejected']:
            flash('Invalid status action.', 'danger')
            return redirect(url_for('tutor_dashboard'))

        if req.status != 'pending':
            flash(f'Cannot change status of a request that is already {req.status}.', 'warning')
            return redirect(url_for('tutor_dashboard'))

        req.status = new_status
        db.session.commit()
        flash(f'Request has been marked as {new_status}.', 'success')
        return redirect(url_for('tutor_dashboard'))

    @app.route('/tutor/request/<int:req_id>/confirm-payment', methods=['POST'])
    @role_required('tutor')
    def tutor_confirm_payment(req_id):
        verify_csrf()
        user = db.session.get(User, session['user_id'])
        profile = user.tutor_profile
        req = db.session.get(TuitionRequest, req_id)

        if not req or req.tutor_id != profile.id:
            flash('Request not found or unauthorized.', 'danger')
            return redirect(url_for('tutor_dashboard'))

        action = request.form.get('action', 'confirm')
        if action == 'confirm':
            req.payment_status = 'payment_confirmed'
            flash('Payment verified and confirmed! Lesson booking is secured.', 'success')
        else:
            req.payment_status = 'unpaid'
            flash('Payment marked as unverified.', 'warning')

        db.session.commit()
        return redirect(url_for('tutor_dashboard'))

    @app.route('/tutor/profile/update', methods=['POST'])
    @role_required('tutor')
    def update_tutor_profile():
        verify_csrf()
        user = db.session.get(User, session['user_id'])
        profile = user.tutor_profile

        headline = request.form.get('headline', '').strip()
        biography = request.form.get('biography', '').strip()
        qualifications = request.form.get('qualifications', '').strip()
        experience_years = request.form.get('experience_years', '').strip()
        hourly_fee = request.form.get('hourly_fee', '').strip()
        teaching_mode = request.form.get('teaching_mode', '').strip()
        languages = request.form.get('languages', '').strip()
        student_levels = request.form.get('student_levels', '').strip()
        availability = request.form.get('availability', '').strip()
        city = request.form.get('city', '').strip()
        upi_id = request.form.get('upi_id', '').strip()
        payment_instructions = request.form.get('payment_instructions', '').strip()
        selected_subjects = request.form.getlist('subjects')

        if not headline or not biography or not hourly_fee:
            flash('Headline, biography, and hourly fee are required.', 'danger')
            return redirect(url_for('tutor_dashboard'))

        try:
            profile.experience_years = int(experience_years)
            profile.hourly_fee = int(hourly_fee)
        except ValueError:
            flash('Invalid number for experience or fee.', 'danger')
            return redirect(url_for('tutor_dashboard'))

        profile.headline = headline
        profile.biography = biography
        profile.qualifications = qualifications
        profile.teaching_mode = teaching_mode or profile.teaching_mode
        profile.languages = languages or profile.languages
        profile.student_levels = student_levels or profile.student_levels
        profile.availability = availability or profile.availability
        profile.upi_id = upi_id
        profile.payment_instructions = payment_instructions
        if city:
            user.city = city

        # Update subjects
        profile.subjects = []
        for sid in selected_subjects:
            subj = db.session.get(Subject, int(sid))
            if subj:
                profile.subjects.append(subj)

        db.session.commit()
        flash('Your tutor profile has been updated successfully.', 'success')
        return redirect(url_for('tutor_dashboard'))

    # ==========================================
    # 8. REST APIS (FOR AJAX / TESTING / FRONTEND)
    # ==========================================
    @app.route('/api/register', methods=['POST'])
    def api_register():
        data = request.get_json(silent=True) or request.form
        full_name = data.get('full_name', '').strip()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        role = data.get('role', 'student').strip().lower()
        city = data.get('city', '').strip()

        if not full_name or not email or not password or not city:
            return jsonify({'error': 'Missing required fields'}), 400

        if role not in ['student', 'tutor']:
            return jsonify({'error': 'Invalid role'}), 400

        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already registered'}), 400

        user = User(full_name=full_name, email=email, role=role, city=city)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()

        if role == 'tutor':
            profile = TutorProfile(
                user_id=user.id,
                headline=data.get('headline', f"Educator in {city}"),
                biography=data.get('biography', 'Experienced tutor ready to guide students.'),
                qualifications=data.get('qualifications', 'Graduate degree'),
                experience_years=int(data.get('experience_years', 1)),
                hourly_fee=int(data.get('hourly_fee', 500)),
                teaching_mode=data.get('teaching_mode', 'Both')
            )
            db.session.add(profile)

        db.session.commit()
        session['user_id'] = user.id
        session['user_role'] = user.role
        session['user_name'] = user.full_name

        return jsonify({'message': 'Registration successful', 'user': user.to_dict()}), 201

    @app.route('/api/login', methods=['POST'])
    def api_login():
        data = request.get_json(silent=True) or request.form
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            return jsonify({'error': 'Invalid email or password'}), 401

        session['user_id'] = user.id
        session['user_role'] = user.role
        session['user_name'] = user.full_name

        return jsonify({'message': 'Login successful', 'user': user.to_dict()}), 200

    @app.route('/api/logout', methods=['POST'])
    def api_logout():
        session.clear()
        return jsonify({'message': 'Logged out successfully'}), 200

    @app.route('/api/me')
    def api_me():
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Not authenticated'}), 401
        user = db.session.get(User, user_id)
        if not user:
            session.clear()
            return jsonify({'error': 'User not found'}), 401
        return jsonify(user.to_dict()), 200

    @app.route('/api/subjects')
    def api_subjects():
        subjects = Subject.query.order_by(Subject.name).all()
        return jsonify([s.to_dict() for s in subjects]), 200

    @app.route('/api/tutors')
    def api_tutors():
        subject = request.args.get('subject')
        city = request.args.get('city')
        min_fee = request.args.get('min_fee')
        max_fee = request.args.get('max_fee')
        page = request.args.get('page', 1, type=int)

        query = TutorProfile.query.join(User)

        if subject:
            if subject.isdigit():
                query = query.filter(TutorProfile.subjects.any(Subject.id == int(subject)))
            else:
                query = query.filter(TutorProfile.subjects.any(Subject.name.ilike(f"%{subject}%")))

        if city:
            query = query.filter(User.city.ilike(f"%{city}%"))

        if min_fee and min_fee.isdigit():
            query = query.filter(TutorProfile.hourly_fee >= int(min_fee))

        if max_fee and max_fee.isdigit():
            query = query.filter(TutorProfile.hourly_fee <= int(max_fee))

        pagination = query.paginate(page=page, per_page=10, error_out=False)
        return jsonify({
            'tutors': [t.to_dict() for t in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': pagination.page
        }), 200

    @app.route('/api/tutors/<int:tutor_id>')
    def api_tutor_detail(tutor_id):
        profile = db.session.get(TutorProfile, tutor_id)
        if not profile:
            return jsonify({'error': 'Tutor not found'}), 404
        return jsonify(profile.to_dict()), 200

    @app.route('/api/requests', methods=['POST'])
    @login_required
    def api_create_request():
        user = db.session.get(User, session['user_id'])
        if user.role != 'student':
            return jsonify({'error': 'Only students can send tuition requests'}), 403

        data = request.get_json(silent=True) or request.form
        tutor_id = data.get('tutor_id')
        profile = db.session.get(TutorProfile, int(tutor_id)) if tutor_id else None
        if not profile:
            return jsonify({'error': 'Tutor not found'}), 404

        req = TuitionRequest(
            student_id=user.id,
            tutor_id=profile.id,
            subject_id=int(data.get('subject_id')) if data.get('subject_id') else None,
            student_level=data.get('student_level', 'High School'),
            teaching_mode=data.get('teaching_mode', 'Online'),
            preferred_schedule=data.get('preferred_schedule', 'Flexible'),
            budget=int(data.get('budget', profile.hourly_fee)),
            message=data.get('message', ''),
            status='pending'
        )
        db.session.add(req)
        db.session.commit()
        return jsonify({'message': 'Request sent successfully', 'request': req.to_dict()}), 201

    @app.route('/api/student/requests')
    @role_required('student')
    def api_student_requests():
        user_id = session['user_id']
        requests = TuitionRequest.query.filter_by(student_id=user_id).order_by(TuitionRequest.created_at.desc()).all()
        return jsonify([r.to_dict() for r in requests]), 200

    @app.route('/api/student/requests/<int:req_id>/cancel', methods=['PATCH', 'POST'])
    @role_required('student')
    def api_cancel_request(req_id):
        user_id = session['user_id']
        req = db.session.get(TuitionRequest, req_id)
        if not req or req.student_id != user_id:
            return jsonify({'error': 'Request not found or unauthorized'}), 404
        if req.status != 'pending':
            return jsonify({'error': 'Only pending requests can be cancelled'}), 400
        req.status = 'cancelled'
        db.session.commit()
        return jsonify({'message': 'Request cancelled successfully', 'request': req.to_dict()}), 200

    @app.route('/api/tutor/requests')
    @role_required('tutor')
    def api_tutor_requests():
        user = db.session.get(User, session['user_id'])
        requests = TuitionRequest.query.filter_by(tutor_id=user.tutor_profile.id).order_by(TuitionRequest.created_at.desc()).all()
        return jsonify([r.to_dict() for r in requests]), 200

    @app.route('/api/tutor/requests/<int:req_id>/status', methods=['PATCH', 'POST'])
    @role_required('tutor')
    def api_update_request_status(req_id):
        user = db.session.get(User, session['user_id'])
        req = db.session.get(TuitionRequest, req_id)
        if not req or req.tutor_id != user.tutor_profile.id:
            return jsonify({'error': 'Request not found or unauthorized'}), 404

        data = request.get_json(silent=True) or request.form
        status = data.get('status', '').lower()
        if status not in ['accepted', 'rejected']:
            return jsonify({'error': 'Invalid status'}), 400
        if req.status != 'pending':
            return jsonify({'error': f'Request is already {req.status}'}), 400

        req.status = status
        db.session.commit()
        return jsonify({'message': f'Request status updated to {status}', 'request': req.to_dict()}), 200

    @app.route('/api/requirements', methods=['GET', 'POST'])
    def api_requirements():
        if request.method == 'POST':
            if 'user_id' not in session:
                return jsonify({'error': 'Authentication required'}), 401
            user = db.session.get(User, session['user_id'])
            if user.role != 'student':
                return jsonify({'error': 'Only students can post requirements'}), 403

            data = request.get_json(silent=True) or request.form
            req = TuitionRequirement(
                student_id=user.id,
                subject_id=int(data.get('subject_id')) if data.get('subject_id') else None,
                student_level=data.get('student_level', 'High School'),
                teaching_mode=data.get('teaching_mode', 'Online'),
                location=data.get('location', user.city),
                budget=int(data.get('budget', 500)),
                preferred_schedule=data.get('preferred_schedule', 'Flexible'),
                description=data.get('description', ''),
                status='open'
            )
            db.session.add(req)
            db.session.commit()
            return jsonify({'message': 'Requirement created', 'requirement': req.to_dict()}), 201

        # GET
        requirements = TuitionRequirement.query.filter_by(status='open').order_by(TuitionRequirement.created_at.desc()).all()
        return jsonify([r.to_dict() for r in requirements]), 200

    # ==========================================
    # ERROR HANDLERS
    # ==========================================
    @app.errorhandler(404)
    def page_not_found(e):
        if request.is_json:
            return jsonify({'error': 'Resource not found'}), 404
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        if request.is_json:
            return jsonify({'error': 'Internal server error'}), 500
        return render_template('500.html'), 500

    return app


app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_database()
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
