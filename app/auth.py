# app/auth.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from .models import User, FingerprintEvent
from .fp_client import fetch_fp_event_by_request_id
from . import db
from flask_login import login_user, logout_user, login_required, current_user
from app.json_utils import to_plain_json

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password']

        # Values passed from the hidden inputs
        fp_visitor_id = (request.form.get('fp_visitorId') or '').strip()
        fp_request_id = (request.form.get('fp_requestId') or '').strip()
        fp_confidence = (request.form.get('fp_confidence') or '').strip()

        # ---- Basic username/email duplicate check ----
        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash('Username or email already exists', 'danger')
            return render_template('register.html')

        # ---- Initialize Fingerprint-related variables so they're always defined ----
        event_data = None
        visitor_id = fp_visitor_id or None          # start with client-provided value
        confidence_val = None
        if fp_confidence:
            try:
                confidence_val = float(fp_confidence)
            except ValueError:
                confidence_val = None

        ip = None
        user_agent = None

        # ---- If we got a requestId, call the Server API and override with server values ----
        if fp_request_id:
            try:
                event_data = fetch_fp_event_by_request_id(fp_request_id)
            except Exception as e:
                current_app.logger.exception("Fingerprint Server API failure: %s", e)

            try:
                prod = (event_data or {}).get("products", {})
                ident = (prod.get("identification") or {}).get("data") or {}

                # Prefer server visitor_id over client
                if ident.get("visitor_id"):
                    visitor_id = ident.get("visitor_id")

                # Prefer server confidence over client
                conf = ident.get("confidence") or {}
                if conf.get("score") is not None:
                    confidence_val = conf.get("score")

                # Correct mapping based on your logged event
                ip = ident.get("ip")
                bd = ident.get("browser_details") or {}
                user_agent = bd.get("user_agent")
            except Exception:
                # Don't break registration if the payload shape changes slightly
                pass

        # ---- Create an event row for *every* registration attempt ----
        safe_event = to_plain_json(event_data) if event_data else None

        evt = FingerprintEvent(
            phase="registration_attempt",           # will update later
            user_id=None,                           # no user yet
            visitor_id=visitor_id or (fp_visitor_id or "unknown"),
            request_id=fp_request_id,
            confidence=confidence_val,
            ip=ip,
            user_agent=user_agent,
            raw_event=safe_event
        )
        db.session.add(evt)   # don't commit yet

        # ---- Enforce one-device-one-account using visitor_id ----
        MIN_CONFIDENCE = 0.8
        if visitor_id and (confidence_val is None or confidence_val >= MIN_CONFIDENCE):
            existing = User.query.filter_by(reg_visitor_id=visitor_id).first()
            if existing:
                # Mark this event as a blocked attempt and commit it
                evt.phase = "registration_blocked"
                db.session.commit()

                flash("This device has already been used to register an account.", "danger")
                return render_template("register.html")

        # ---- Create user (now visitor_id is definitely defined) ----
        user = User(username=username, email=email)
        user.set_password(password)
        user.reg_visitor_id = visitor_id  # can be None if we didn't get anything
        db.session.add(user)
        db.session.commit()

        # ---- Link the event to the user and mark as successful registration ----
        evt.user_id = user.id
        evt.phase = "registration"
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
