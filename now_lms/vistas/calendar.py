# Copyright 2025 BMO Soluciones, S.A.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""Calendar views for student users."""

import calendar as cal

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from flask import Blueprint, Response, abort, render_template, request
from flask_login import current_user, login_required

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.config import DIRECTORIO_PLANTILLAS
from now_lms.db import UserEvent, database

calendar = Blueprint("calendar", __name__, template_folder=DIRECTORIO_PLANTILLAS)


@calendar.route("/user/calendar")
@login_required
def calendar_view():
    """Display the user's calendar with events."""
    # Get current year and month from request, default to current
    now = datetime.now()
    year = request.args.get("year", now.year, type=int)
    month = request.args.get("month", now.month, type=int)

    # Validate year and month parameters
    if year < 1 or year > 9999:
        year = now.year
    if month < 1 or month > 12:
        month = now.month

    # Create calendar
    cal_obj = cal.Calendar(firstweekday=0)  # Monday first
    month_days = cal_obj.monthdayscalendar(year, month)

    # Get events for this month
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)

    events = (
        database.session.execute(
            database.select(UserEvent)
            .filter(UserEvent.user_id == current_user.usuario)
            .filter(UserEvent.start_time >= start_date)
            .filter(UserEvent.start_time < end_date)
            .order_by(UserEvent.start_time)
        )
        .scalars()
        .all()
    )

    # Group events by day
    events_by_day = {}
    for event in events:
        day = event.start_time.day
        if day not in events_by_day:
            events_by_day[day] = []
        events_by_day[day].append(event)

    # Navigation dates
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1

    month_name = cal.month_name[month]

    return render_template(
        "calendar/calendar_view.html",
        month_days=month_days,
        events_by_day=events_by_day,
        year=year,
        month=month,
        month_name=month_name,
        prev_year=prev_year,
        prev_month=prev_month,
        next_year=next_year,
        next_month=next_month,
    )


@calendar.route("/user/calendar/event/<event_id>")
@login_required
def event_detail(event_id):
    """Display details for a specific event."""
    event = database.session.execute(
        database.select(UserEvent).filter(UserEvent.id == event_id).filter(UserEvent.user_id == current_user.usuario)
    ).scalar_one_or_none()

    if not event:
        abort(404)

    return render_template("calendar/event_detail.html", event=event)


@calendar.route("/user/calendar/export.ics")
@login_required
def export_ics():
    """Export user's calendar events as ICS file."""
    # Get all future events for the user
    now = datetime.now()
    events = (
        database.session.execute(
            database.select(UserEvent)
            .filter(UserEvent.user_id == current_user.usuario)
            .filter(UserEvent.start_time >= now)
            .order_by(UserEvent.start_time)
        )
        .scalars()
        .all()
    )

    # Generate ICS content
    ics_content = _generate_ics_content(events)

    return Response(
        ics_content,
        mimetype="text/calendar",
        headers={"Content-Disposition": f"attachment; filename=calendar-{current_user.usuario}.ics"},
    )


def _generate_ics_content(events):
    """Generate ICS calendar content from events."""
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//NOW LMS//Calendar//EN", "CALSCALE:GREGORIAN", "METHOD:PUBLISH"]

    for event in events:
        # Convert to UTC for ICS format if timezone is specified
        start_time = event.start_time
        end_time = event.end_time or event.start_time + timedelta(hours=1)

        # If event has timezone info, handle accordingly
        if event.timezone and event.timezone != "UTC":
            try:
                import pytz

                local_tz = pytz.timezone(event.timezone)
                utc_tz = pytz.UTC

                # If datetime is naive, assume it's in the event's timezone
                if start_time.tzinfo is None:
                    start_time = local_tz.localize(start_time).astimezone(utc_tz)
                if end_time.tzinfo is None:
                    end_time = local_tz.localize(end_time).astimezone(utc_tz)
            except ImportError:
                # pytz not available, use times as-is
                pass
            except Exception:
                # Invalid timezone or other error, use times as-is
                pass

        # Format datetime for ICS (UTC)
        start_dt = start_time.strftime("%Y%m%dT%H%M%SZ")
        end_dt = end_time.strftime("%Y%m%dT%H%M%SZ")
        # Use event creation timestamp for DTSTAMP field
        created_dt = event.timestamp.strftime("%Y%m%dT%H%M%SZ")

        # Escape special characters in text fields
        title = _escape_ics_text(event.title)
        description = _escape_ics_text(event.description or "")

        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:{event.id}@nowlms.local",
                f"DTSTART:{start_dt}",
                f"DTEND:{end_dt}",
                f"DTSTAMP:{created_dt}",
                f"SUMMARY:{title}",
                f"DESCRIPTION:{description}",
                f'STATUS:{"CONFIRMED" if event.status == "confirmed" else "TENTATIVE"}',
                "END:VEVENT",
            ]
        )

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines)


def _escape_ics_text(text):
    """Escape text for ICS format."""
    if not text:
        return ""
    return text.replace("\\", "\\\\").replace(",", "\\,").replace(";", "\\;").replace("\n", "\\n")


@calendar.route("/user/calendar/upcoming")
@login_required
def upcoming_events():
    """Get upcoming events for dashboard display."""
    now = datetime.now()
    events = (
        database.session.execute(
            database.select(UserEvent)
            .filter(UserEvent.user_id == current_user.usuario)
            .filter(UserEvent.start_time >= now)
            .order_by(UserEvent.start_time)
            .limit(5)
        )
        .scalars()
        .all()
    )

    return render_template("calendar/upcoming_events.html", events=events)
