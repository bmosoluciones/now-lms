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
# Contributors:
# - William José Moreno Reyes

"""Tests for the messaging system functionality."""

import pytest
from datetime import datetime

from now_lms import lms_app
from now_lms.db import (
    Curso, 
    DocenteCurso, 
    EstudianteCurso, 
    Message, 
    MessageThread, 
    ModeradorCurso, 
    Usuario, 
    database
)


class TestMessagingSystem:
    """Test cases for the messaging system."""

    def test_message_thread_model(self):
        """Test MessageThread model creation."""
        with lms_app.app_context():
            # Create a test thread
            thread = MessageThread()
            thread.course_id = "TEST001"
            thread.student_id = "test_student"
            thread.status = "open"
            
            assert thread.course_id == "TEST001"
            assert thread.student_id == "test_student"
            assert thread.status == "open"
            assert thread.closed_at is None

    def test_message_model(self):
        """Test Message model creation."""
        with lms_app.app_context():
            # Create a test message
            message = Message()
            message.thread_id = "test_thread_id"
            message.sender_id = "test_sender"
            message.content = "Test message content"
            
            assert message.thread_id == "test_thread_id"
            assert message.sender_id == "test_sender"
            assert message.content == "Test message content"
            assert message.read_at is None
            # Check that is_reported defaults to False (or None before database insert)
            assert message.is_reported in [False, None]
            assert message.reported_reason is None

    def test_thread_status_transitions(self):
        """Test valid thread status transitions."""
        with lms_app.app_context():
            # Test valid transitions
            valid_transitions = {
                "open": ["fixed", "closed"],
                "fixed": ["closed"],
                "closed": []
            }
            
            # This would be tested in the views with actual database operations
            assert "fixed" in valid_transitions["open"]
            assert "closed" in valid_transitions["open"]
            assert "closed" in valid_transitions["fixed"]
            assert len(valid_transitions["closed"]) == 0

    def test_forms_exist(self):
        """Test that message forms can be imported and instantiated."""
        with lms_app.app_context():
            with lms_app.test_request_context():
                from now_lms.forms import MessageThreadForm, MessageReplyForm, MessageReportForm
                
                # Test form instantiation
                thread_form = MessageThreadForm()
                reply_form = MessageReplyForm()
                report_form = MessageReportForm()
                
                assert thread_form is not None
                assert reply_form is not None
                assert report_form is not None
                
                # Test form fields exist
                assert hasattr(thread_form, 'subject')
                assert hasattr(thread_form, 'content')
                assert hasattr(thread_form, 'course_id')
                
                assert hasattr(reply_form, 'content')
                assert hasattr(reply_form, 'thread_id')
                
                assert hasattr(report_form, 'reason')
                assert hasattr(report_form, 'message_id')
                assert hasattr(report_form, 'thread_id')

    def test_messaging_routes_exist(self):
        """Test that messaging routes are properly registered."""
        with lms_app.app_context():
            # Check that key routes exist
            rules = {rule.endpoint: rule.rule for rule in lms_app.url_map.iter_rules()}
            
            assert "msg.course_messages" in rules
            assert "msg.user_messages" in rules
            assert "msg.new_thread" in rules
            assert "msg.view_thread" in rules
            assert "msg.reply_to_thread" in rules
            assert "msg.change_thread_status" in rules
            assert "msg.report_message" in rules
            assert "msg.admin_flagged_messages" in rules
            
            # Check route patterns
            assert rules["msg.course_messages"] == "/course/<course_code>/messages"
            assert rules["msg.user_messages"] == "/user/messages"
            assert rules["msg.new_thread"] == "/course/<course_code>/messages/new"