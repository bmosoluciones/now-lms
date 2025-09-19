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

"""Demo mode functionality for NOW LMS."""


from __future__ import annotations

# ---------------------------------------------------------------------------------------
# Third-party libraries
# ---------------------------------------------------------------------------------------
from flask import flash
from flask_login import current_user

# ---------------------------------------------------------------------------------------
# Local resources
# ---------------------------------------------------------------------------------------
from now_lms.i18n import _


def is_demo_mode() -> bool:
    """Check if the system is running in demo mode."""
    from os import environ

    from now_lms.config import VALORES_TRUE

    return environ.get("NOW_LMS_DEMO_MODE", "0").strip().lower() in VALORES_TRUE


def is_admin_user() -> bool:
    """Check if current user is an admin."""
    try:
        return current_user.is_authenticated and current_user.tipo == "admin"
    except (AttributeError, RuntimeError):
        # Handle cases where current_user is not available (outside request context)
        return False


def check_demo_admin_restriction() -> bool:
    """
    Check if current admin action should be restricted in demo mode.

    Returns:
        True if action should be blocked (demo mode + admin user)
        False if action should be allowed
    """
    return is_demo_mode() and is_admin_user()


def flash_demo_restriction_message():
    """Flash a message indicating the action is restricted in demo mode."""
    flash(_("Esta acción no está disponible en modo demostración para prevenir uso abusivo."), "warning")


def demo_restriction_check(action_name: str | None = None) -> bool:
    """
    Decorator-like function to check demo mode restrictions and flash message.

    Args:
        action_name: Optional name of the action for logging

    Returns:
        True if action should be blocked, False if it should proceed
    """
    if check_demo_admin_restriction():
        flash_demo_restriction_message()
        return True
    return False
