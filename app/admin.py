# app/admin.py
from flask import Blueprint, render_template, request, abort
from flask_login import login_required, current_user

from .models import FingerprintEvent

bp = Blueprint("admin", __name__, url_prefix="/admin")


def _admin_required():
    """Simple helper to enforce admin access."""
    if not current_user.is_authenticated or not getattr(current_user, "is_admin", False):
        abort(403)


@bp.route("/fp-events")
@login_required
def fp_events():
    _admin_required()

    # pagination params
    page = request.args.get("page", 1, type=int)
    per_page = 20

    # optional filters
    phase = request.args.get("phase", "", type=str).strip()
    visitor_id = request.args.get("visitor_id", "", type=str).strip()

    query = FingerprintEvent.query.order_by(FingerprintEvent.created_at.desc())

    if phase:
        query = query.filter(FingerprintEvent.phase == phase)
    if visitor_id:
        query = query.filter(FingerprintEvent.visitor_id == visitor_id)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    events = pagination.items

    return render_template(
        "admin_fp_events.html",
        events=events,
        pagination=pagination,
        phase=phase,
        visitor_id_filter=visitor_id
    )


@bp.route("/fp-events/<int:event_id>")
@login_required
def fp_event_detail(event_id):
    _admin_required()

    event = FingerprintEvent.query.get_or_404(event_id)
    return render_template('admin_fp_event_detail.html', event=event)