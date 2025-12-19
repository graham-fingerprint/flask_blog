# app/auth.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from .models import User, FingerprintEvent
from .fp_client import fetch_fp_event_by_request_id
from . import db
from flask_login import login_user, logout_user, login_required, current_user
from app.json_utils import to_plain_json
from .sealed_fp import unseal_fp_events_response

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password']

        # ---- Hidden fields ----
        fp_sealed = (request.form.get('fp_sealed_result') or '').strip()
        fp_request_id = (request.form.get('fp_requestId') or '').strip()  # optional, for logging/fallback later

        # ---- Basic duplicate checks ----
        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash('Username or email already exists', 'danger')
            return render_template('register.html')

        # ---- Initialize FP vars ----
        fp_verified = False
        visitor_id = None
        confidence_val = None
        ip = None
        user_agent = None
        event_data = None

        # ---- Unseal the sealedResult on the backend ----
        if fp_sealed:
            try:
                events_response = unseal_fp_events_response(fp_sealed)
                # events_response has the same structure as /events
                # Typically: events_response.products.identification.data
                products = getattr(events_response, "products", None) or {}
                ident = (products.get("identification") or {}).get("data") or {}

                visitor_id = ident.get("visitor_id")
                conf = ident.get("confidence") or {}
                confidence_val = conf.get("score")

                ip = ident.get("ip")
                bd = ident.get("browser_details") or {}
                user_agent = bd.get("user_agent")

                # For logging, we might want a plain dict form of the response
                # depending on how your JSON serializer works. Many SDK models
                # have a to_dict() method.
                event_data = events_response.to_dict() if hasattr(events_response, "to_dict") else None

                if visitor_id:
                    fp_verified = True
            except Exception as e:
                current_app.logger.exception("Failed to unseal Fingerprint sealedResult: %s", e)

        # ---- Log the attempt ----
        safe_event = to_plain_json(event_data) if event_data else None

        evt = FingerprintEvent(
            phase="registration_attempt",
            user_id=None,
            visitor_id=visitor_id or "unverified",
            request_id=fp_request_id,      # still useful for debugging / replay protection
            confidence=confidence_val,
            ip=ip,
            user_agent=user_agent,
            raw_event=safe_event,
        )
        db.session.add(evt)

        # ---- Enforce one-device-one-account ONLY if sealed data is verified ----
        if fp_verified and visitor_id:
            MIN_CONFIDENCE = 0.8
            if confidence_val is None or confidence_val >= MIN_CONFIDENCE:
                existing = User.query.filter_by(reg_visitor_id=visitor_id).first()
                if existing:
                    evt.phase = "registration_blocked"
                    db.session.commit()
                    flash("This device has already been used to register an account.", "danger")
                    return render_template("register.html")

        # ---- Create user ----
        user = User(username=username, email=email)
        user.set_password(password)

        # Tie this device to the user only if we have verified device identity
        if fp_verified and visitor_id:
            user.reg_visitor_id = visitor_id

        db.session.add(user)
        db.session.commit()

        # ---- Update event with user info & final phase ----
        evt.user_id = user.id
        evt.phase = "registration" if fp_verified else "registration_unverified"
        db.session.commit()

        flash('Registration successful — please log in', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username_or_email = request.form['username'].strip()
        password = request.form['password']
        user = User.query.filter((User.username == username_or_email) | (User.email == username_or_email)).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully', 'success')
            next_page = request.args.get('next') or url_for('main.index')
            return redirect(next_page)
        flash('Invalid credentials', 'danger')
    return render_template('login.html')

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.index'))
