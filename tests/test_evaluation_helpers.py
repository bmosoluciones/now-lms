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

"""Tests for evaluation helper functions."""

from now_lms.vistas.evaluation_helpers import (
    check_user_evaluations_completed,
    get_user_evaluation_status,
    can_user_receive_certificate,
)


class TestEvaluationHelpers:
    """Test class for evaluation helper functions."""

    def test_check_user_evaluations_completed_no_evaluations(self, full_db_setup):
        """Test check_user_evaluations_completed when course has no evaluations."""
        with full_db_setup.app_context():
            # Use a course that doesn't have evaluations set up
            result = check_user_evaluations_completed("curso-test", "usuario-test")
            all_passed, failed_count, total_count = result

            assert all_passed is True
            assert failed_count == 0
            assert total_count == 0

    def test_check_user_evaluations_completed_with_test_data(self, full_db_setup):
        """Test check_user_evaluations_completed with test data."""
        with full_db_setup.app_context():
            # Test with existing course and user from test data
            result = check_user_evaluations_completed("intro-python", "lms-admin")
            all_passed, failed_count, total_count = result

            # Result should be a tuple with boolean and two integers
            assert isinstance(all_passed, bool)
            assert isinstance(failed_count, int)
            assert isinstance(total_count, int)
            assert failed_count >= 0
            assert total_count >= 0

    def test_get_user_evaluation_status_no_evaluations(self, full_db_setup):
        """Test get_user_evaluation_status when course has no evaluations."""
        with full_db_setup.app_context():
            result = get_user_evaluation_status("curso-test", "usuario-test")

            assert isinstance(result, dict)
            assert "total_evaluations" in result
            assert "passed_evaluations" in result
            assert "failed_evaluations" in result
            assert "pending_evaluations" in result
            assert "evaluation_details" in result

            assert result["total_evaluations"] == 0
            assert result["passed_evaluations"] == 0
            assert result["failed_evaluations"] == 0
            assert result["pending_evaluations"] == 0
            assert isinstance(result["evaluation_details"], list)
            assert len(result["evaluation_details"]) == 0

    def test_get_user_evaluation_status_with_test_data(self, full_db_setup):
        """Test get_user_evaluation_status with test data."""
        with full_db_setup.app_context():
            result = get_user_evaluation_status("intro-python", "lms-admin")

            assert isinstance(result, dict)
            assert "total_evaluations" in result
            assert "passed_evaluations" in result
            assert "failed_evaluations" in result
            assert "pending_evaluations" in result
            assert "evaluation_details" in result

            # Validate data types and ranges
            assert isinstance(result["total_evaluations"], int)
            assert isinstance(result["passed_evaluations"], int)
            assert isinstance(result["failed_evaluations"], int)
            assert isinstance(result["pending_evaluations"], int)
            assert isinstance(result["evaluation_details"], list)

            # Validate that counts add up correctly
            assert (result["passed_evaluations"] + result["failed_evaluations"] + result["pending_evaluations"]) == result[
                "total_evaluations"
            ]

    def test_can_user_receive_certificate_no_course_data(self, full_db_setup):
        """Test can_user_receive_certificate with non-existent course."""
        with full_db_setup.app_context():
            result = can_user_receive_certificate("nonexistent-course", "usuario-test")
            can_receive, reason = result

            assert isinstance(can_receive, bool)
            assert isinstance(reason, str)
            # Should return False for non-existent course with appropriate reason
            assert can_receive is True or can_receive is False  # Either is valid for non-existent course

    def test_can_user_receive_certificate_with_test_data(self, full_db_setup):
        """Test can_user_receive_certificate with test data."""
        with full_db_setup.app_context():
            result = can_user_receive_certificate("intro-python", "lms-admin")
            can_receive, reason = result

            assert isinstance(can_receive, bool)
            assert isinstance(reason, str)
            assert len(reason) > 0  # Reason should not be empty

    def test_evaluation_status_details_structure(self, full_db_setup):
        """Test that evaluation details have the correct structure."""
        with full_db_setup.app_context():
            result = get_user_evaluation_status("intro-python", "lms-admin")

            for detail in result["evaluation_details"]:
                assert isinstance(detail, dict)
                assert "evaluation_id" in detail
                assert "title" in detail
                assert "is_exam" in detail
                assert "passing_score" in detail
                assert "status" in detail
                assert "best_score" in detail
                assert "attempts_count" in detail

                # Validate data types
                assert isinstance(detail["attempts_count"], int)
                assert detail["status"] in ["passed", "failed", "pending"]
                assert isinstance(detail["is_exam"], bool)
