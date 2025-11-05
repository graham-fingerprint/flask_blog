# app/routes.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from .models import Post, FingerprintEvent
from . import db
from datetime import datetime
from flask_login import login_required, current_user

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    posts = Post.query.order_by(Post.created_at.desc()).all()
    return render_template('index.html', posts=posts)

@bp.route('/post/<int:post_id>')
def post_view(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', post=post)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == 'POST':
        title = request.form['title'].strip()
        body = request.form['body'].strip()
        if not title or not body:
            flash('Title and body required', 'danger')
            return render_template('create_post.html')
        post = Post(title=title, body=body, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Post created', 'success')
        return redirect(url_for('main.post_view', post_id=post.id))
    return render_template('create_post.html')

@bp.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    if request.method == 'POST':
        post.title = request.form['title'].strip()
        post.body = request.form['body'].strip()
        db.session.commit()
        flash('Post updated', 'success')
        return redirect(url_for('main.post_view', post_id=post.id))
    return render_template('create_post.html', post=post)

@bp.route('/admin/fp-events')
@login_required
def fp_events():
    events = FingerprintEvent.query.order_by(FingerprintEvent.created_at.desc()).limit(50).all()
    return render_template('fp_events.html', events=events)

class FingerprintEvent(db.Model):
    __tablename__ = "fingerprint_events"

    id = db.Column(db.Integer, primary_key=True)
    phase = db.Column(db.String(32), nullable=False, default="registration")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    visitor_id = db.Column(db.String(128), index=True, nullable=False)
    request_id = db.Column(db.String(128), index=True, nullable=False)

    confidence = db.Column(db.Float)
    ip = db.Column(db.String(64))
    user_agent = db.Column(db.Text)

    raw_event = db.Column(db.JSON)  # JSONB in Postgres; perfect for full payloads
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
