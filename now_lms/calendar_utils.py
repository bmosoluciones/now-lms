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

"""Utilities for managing user calendar events."""

import threading

# ---------------------------------------------------------------------------------------
# Standard library
# ---------------------------------------------------------------------------------------
from datetime import datetime, time

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from flask import current_app

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.db import CursoRecurso, CursoSeccion, Evaluation, UserEvent, database
from now_lms.logs import log


def create_events_for_student_enrollment(user_id, course_id):
    """Create calendar events when a student enrolls in a course."""
    try:
        # Get course resources of type 'meet' with dates
        meet_resources = (
            database.session.execute(
                database.select(CursoRecurso)
                .filter(CursoRecurso.curso == course_id)
                .filter(CursoRecurso.tipo == "meet")
                .filter(CursoRecurso.fecha.is_not(None))
            )
            .scalars()
            .all()
        )

        # Get evaluations with deadlines
        evaluations = (
            database.session.execute(
                database.select(Evaluation)
                .join(Evaluation.section)
                .filter(CursoSeccion.curso == course_id)
                .filter(Evaluation.available_until.is_not(None))
            )
            .scalars()
            .all()
        )

        events_created = 0

        # Create events for meet resources
        for resource in meet_resources:
            start_time = _combine_date_time(resource.fecha, resource.hora_inicio)
            end_time = _combine_date_time(resource.fecha, resource.hora_fin) if resource.hora_fin else None

            # Check if event already exists
            existing_event = database.session.execute(
                database.select(UserEvent).filter(UserEvent.user_id == user_id).filter(UserEvent.resource_id == resource.id)
            ).scalar_one_or_none()

            if not existing_event:
                event = UserEvent(
                    user_id=user_id,
                    course_id=course_id,
                    section_id=resource.seccion,
                    resource_id=resource.id,
                    resource_type="meet",
                    title=resource.nombre,
                    description=resource.descripcion,
                    start_time=start_time,
                    end_time=end_time,
                    timezone=_get_app_timezone(),
                    status="pending",
                )
                database.session.add(event)
                events_created += 1

        # Create events for evaluations
        for evaluation in evaluations:
            # Check if event already exists
            existing_event = database.session.execute(
                database.select(UserEvent)
                .filter(UserEvent.user_id == user_id)
                .filter(UserEvent.evaluation_id == evaluation.id)
            ).scalar_one_or_none()

            if not existing_event:
                event = UserEvent(
                    user_id=user_id,
                    course_id=course_id,
                    section_id=evaluation.section_id,
                    evaluation_id=evaluation.id,
                    resource_type="evaluation",
                    title=f"Fecha límite: {evaluation.title}",
                    description=evaluation.description,
                    start_time=evaluation.available_until,
                    timezone=_get_app_timezone(),
                    status="pending",
                )
                database.session.add(event)
                events_created += 1

        database.session.commit()
        log.info(f"Created {events_created} calendar events for user {user_id} in course {course_id}")

    except Exception as e:
        log.error(f"Error creating calendar events for user {user_id} in course {course_id}: {e}")
        database.session.rollback()


def update_meet_resource_events(resource_id):
    """Update all user events when a meet resource is modified."""

    def _update_in_background():
        try:
            app = current_app._get_current_object()
            with app.app_context():
                # Get the updated resource
                resource = database.session.execute(
                    database.select(CursoRecurso).filter(CursoRecurso.id == resource_id)
                ).scalar_one_or_none()

                if not resource or resource.tipo != "meet":
                    return

                # Get all events related to this resource
                events = (
                    database.session.execute(database.select(UserEvent).filter(UserEvent.resource_id == resource_id))
                    .scalars()
                    .all()
                )

                updates_made = 0
                for event in events:
                    # Update event details
                    start_time = _combine_date_time(resource.fecha, resource.hora_inicio)
                    end_time = _combine_date_time(resource.fecha, resource.hora_fin) if resource.hora_fin else None

                    event.title = resource.nombre
                    event.description = resource.descripcion
                    event.start_time = start_time
                    event.end_time = end_time
                    event.timezone = _get_app_timezone()
                    updates_made += 1

                database.session.commit()
                log.info(f"Updated {updates_made} calendar events for resource {resource_id}")

        except Exception as e:
            log.error(f"Error updating calendar events for resource {resource_id}: {e}")

            database.session.rollback()

    # Run update in background thread
    thread = threading.Thread(target=_update_in_background)
    thread.daemon = True
    thread.start()


def update_evaluation_events(evaluation_id):
    """Update all user events when an evaluation deadline is modified."""

    def _update_in_background():
        try:
            app = current_app._get_current_object()
            with app.app_context():
                # Get the updated evaluation
                evaluation = database.session.execute(
                    database.select(Evaluation).filter(Evaluation.id == evaluation_id)
                ).scalar_one_or_none()

                if not evaluation:
                    return

                # Get all events related to this evaluation
                events = (
                    database.session.execute(database.select(UserEvent).filter(UserEvent.evaluation_id == evaluation_id))
                    .scalars()
                    .all()
                )

                updates_made = 0
                for event in events:
                    # Update event details
                    event.title = f"Fecha límite: {evaluation.title}"
                    event.description = evaluation.description
                    event.start_time = evaluation.available_until
                    event.timezone = _get_app_timezone()
                    updates_made += 1

                database.session.commit()
                log.info(f"Updated {updates_made} calendar events for evaluation {evaluation_id}")

        except Exception as e:
            log.error(f"Error updating calendar events for evaluation {evaluation_id}: {e}")

            database.session.rollback()

    # Run update in background thread
    thread = threading.Thread(target=_update_in_background)
    thread.daemon = True
    thread.start()


def get_upcoming_events_for_user(user_id, limit=5):
    """Get upcoming events for a user (for dashboard display)."""
    # Handle invalid inputs
    if not user_id or limit <= 0:
        return []

    now = datetime.now()
    query = (
        database.select(UserEvent)
        .filter(UserEvent.user_id == user_id)
        .filter(UserEvent.start_time >= now)
        .order_by(UserEvent.start_time)
    )

    # Only apply limit if it's positive to avoid MySQL syntax errors
    if limit > 0:
        query = query.limit(limit)

    events = database.session.execute(query).scalars().all()
    return events


def _combine_date_time(date_obj, time_obj):
    """Combine date and time objects into datetime."""
    if not date_obj:
        return None

    if not time_obj:
        time_obj = time(9, 0)  # Default to 9:00 AM

    return datetime.combine(date_obj, time_obj)


def _get_app_timezone():
    """Get the application's configured timezone."""
    from now_lms.i18n import get_timezone

    return get_timezone()


def cleanup_events_for_course_unenrollment(user_id, course_id):
    """Remove calendar events when a student unenrolls from a course."""
    try:
        # Delete all events for this user and course
        events_to_delete = (
            database.session.execute(
                database.select(UserEvent).filter(UserEvent.user_id == user_id).filter(UserEvent.course_id == course_id)
            )
            .scalars()
            .all()
        )

        count = len(events_to_delete)
        for event in events_to_delete:
            database.session.delete(event)

        database.session.commit()
        log.info(f"Removed {count} calendar events for user {user_id} unenrolling from course {course_id}")

    except Exception as e:
        log.error(f"Error removing calendar events for user {user_id} from course {course_id}: {e}")
        database.session.rollback()
