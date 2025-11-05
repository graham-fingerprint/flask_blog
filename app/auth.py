# app/auth.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from .models import User, FingerprintEvent
from .fp_client import fetch_fp_event_by_request_id
from . import db
from flask_login import login_user, logout_user, login_required, current_user

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password']
        
        # Values passed from the hidden inputs
        fp_visitor_id = request.form.get('fp_visitorId', '').strip()
        fp_request_id = request.form.get('fp_requestId', '').strip()
        fp_confidence = request.form.get('fp_confidence', '').strip()
        
        # dupe check
        if User.query.filter((User.username == username) | (User.email == email)).first():
            flash('Username or email already exists', 'danger')
            return render_template('register.html')
        
        #create user
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        # If we got a requestId, call the Server API, then store the event
        if fp_request_id:
            event_data = None
            try:
                event_data = fetch_fp_event_by_request_id(fp_request_id)
            except Exception as e:
                current_app.logger.exception("Fingerprint Server API failure: %s", e)

            # Extract a few commonly useful fields (raw_event keeps everything)
            ip = None
            user_agent = None
            confidence_val = None
            visitor_id = fp_visitor_id or None
            try:
                # these keys may vary; guard with .get()
                prod = (event_data or {}).get("products", {})
                ident = (prod.get("identification") or {}).get("data") or {}
                if not visitor_id:
                    visitor_id = ident.get("visitor_id")
                conf = ident.get("confidence") or {}
                confidence_val = conf.get("score")
                ip = (event_data or {}).get("ip")
                # some SDKs nest UA differently
                user_agent = ((event_data or {}).get("browser_details") or
                              (event_data or {}).get("client") or {}).get("user_agent")
            except Exception:
                pass

            # Store in DB (fallback to "unknown" if visitor_id is empty)
            evt = FingerprintEvent(
                phase="registration",
                user_id=user.id,
                visitor_id=visitor_id or "unknown",
                request_id=fp_request_id,
                confidence=confidence_val or (float(fp_confidence) if fp_confidence else None),
                ip=ip,
                user_agent=user_agent,
                raw_event=event_data
            )
            db.session.add(evt)
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
