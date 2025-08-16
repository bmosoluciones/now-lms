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


"""Simple negative tests for core modules to increase code coverage."""

import jwt
from unittest.mock import Mock, patch


class TestSimpleNegativeCases:
    """Test simple negative cases and edge conditions for core modules."""

    def test_auth_validar_acceso_nonexistent_user(self, lms_application):
        """Test validar_acceso with nonexistent user."""
        from now_lms.auth import validar_acceso

        with lms_application.app_context():
            # Test with username that doesn't exist
            result = validar_acceso("nonexistent_user", "any_password")
            assert result is False

            # Test with email that doesn't exist
            result = validar_acceso("nonexistent@email.com", "any_password")
            assert result is False

    def test_auth_validate_password_reset_token_decode_error(self, lms_application):
        """Test validate_password_reset_token with decode error."""
        from now_lms.auth import validate_password_reset_token

        with lms_application.app_context():
            # Test with malformed token
            result = validate_password_reset_token("malformed.token.data")
            assert result is None

            # Test with completely invalid token
            result = validate_password_reset_token("invalid_token")
            assert result is None

    def test_auth_validate_password_reset_token_missing_fields(self, lms_application):
        """Test validate_password_reset_token with missing required fields."""
        from now_lms.auth import validate_password_reset_token

        with lms_application.app_context():
            # Token without reset_email
            token_no_email = jwt.encode({"action": "password_reset"}, lms_application.secret_key, algorithm="HS512")
            result = validate_password_reset_token(token_no_email)
            assert result is None

            # Token without action
            token_no_action = jwt.encode({"reset_email": "test@example.com"}, lms_application.secret_key, algorithm="HS512")
            result = validate_password_reset_token(token_no_action)
            assert result is None

            # Token with wrong action
            token_wrong_action = jwt.encode(
                {"reset_email": "test@example.com", "action": "other_action"}, lms_application.secret_key, algorithm="HS512"
            )
            result = validate_password_reset_token(token_wrong_action)
            assert result is None

    def test_auth_validate_confirmation_token_expired(self, lms_application):
        """Test validate_confirmation_token with expired token."""
        from now_lms.auth import validate_confirmation_token

        with lms_application.app_context():
            # Create expired token
            expired_token = jwt.encode(
                {"exp": 0, "confirm_id": "test@example.com"}, lms_application.secret_key, algorithm="HS512"  # Expired
            )

            result = validate_confirmation_token(expired_token)
            assert result is False

    def test_auth_validate_confirmation_token_invalid_signature(self, lms_application):
        """Test validate_confirmation_token with invalid signature."""
        from now_lms.auth import validate_confirmation_token

        with lms_application.app_context():
            # Create token with wrong secret
            invalid_token = jwt.encode({"confirm_id": "test@example.com"}, "wrong_secret", algorithm="HS512")

            result = validate_confirmation_token(invalid_token)
            assert result is False

    def test_auth_validate_confirmation_token_missing_confirm_id(self, lms_application):
        """Test validate_confirmation_token with missing confirm_id."""
        from now_lms.auth import validate_confirmation_token

        with lms_application.app_context():
            # Create token without confirm_id
            token = jwt.encode({"other_field": "value"}, lms_application.secret_key, algorithm="HS512")

            result = validate_confirmation_token(token)
            assert result is False

    def test_auth_proteger_passwd_edge_cases(self):
        """Test proteger_passwd with edge cases."""
        from now_lms.auth import proteger_passwd

        # Test with empty password
        result = proteger_passwd("")
        assert result is not None
        assert len(result) > 0

        # Test with very long password
        long_password = "a" * 500
        result = proteger_passwd(long_password)
        assert result is not None
        assert len(result) > 0

    def test_cache_no_guardar_en_cache_global_with_authenticated_user(self, lms_application):
        """Test no_guardar_en_cache_global when user is authenticated."""
        from now_lms.cache import no_guardar_en_cache_global

        with lms_application.app_context():
            # Mock current_user as authenticated
            with patch("now_lms.cache.current_user") as mock_user:
                mock_user.is_authenticated = True

                result = no_guardar_en_cache_global()
                assert result is True

    def test_cache_no_guardar_en_cache_global_with_unauthenticated_user(self, lms_application):
        """Test no_guardar_en_cache_global when user is not authenticated."""
        from now_lms.cache import no_guardar_en_cache_global

        with lms_application.app_context():
            # Mock current_user as not authenticated
            with patch("now_lms.cache.current_user") as mock_user:
                mock_user.is_authenticated = False

                result = no_guardar_en_cache_global()
                assert result is False

    def test_cache_no_guardar_en_cache_global_with_none_user(self, lms_application):
        """Test no_guardar_en_cache_global when current_user is None."""
        from now_lms.cache import no_guardar_en_cache_global

        with lms_application.app_context():
            # Mock current_user as None
            with patch("now_lms.cache.current_user", None):
                result = no_guardar_en_cache_global()
                # When current_user is None, it returns None which is falsy
                assert result is None or result is False

    def test_cache_invalidate_all_cache_with_null_cache(self, lms_application):
        """Test invalidate_all_cache when using NullCache."""
        from now_lms.cache import invalidate_all_cache

        with lms_application.app_context():
            # Mock CTYPE as NullCache
            with patch("now_lms.cache.CTYPE", "NullCache"):
                result = invalidate_all_cache()
                assert result is True

    def test_cache_invalidate_all_cache_with_redis_cache_failure(self, lms_application):
        """Test invalidate_all_cache when Redis cache clear fails."""
        from now_lms.cache import invalidate_all_cache

        with lms_application.app_context():
            # Mock CTYPE as RedisCache and cache clear raises exception
            with patch("now_lms.cache.CTYPE", "RedisCache"):
                with patch("now_lms.cache.cache.clear") as mock_clear:
                    mock_clear.side_effect = Exception("Redis connection failed")

                    result = invalidate_all_cache()
                    assert result is False
                    mock_clear.assert_called_once()

    def test_mail_load_mail_config_from_env_incomplete_config(self, lms_application):
        """Test _load_mail_config_from_env with incomplete environment variables."""
        from now_lms.mail import _load_mail_config_from_env
        import os

        with lms_application.app_context():
            # Clear environment variables
            env_vars = ["MAIL_SERVER", "MAIL_PORT", "MAIL_USERNAME", "MAIL_PASSWORD"]
            original_values = {}
            for var in env_vars:
                original_values[var] = os.environ.get(var)
                if var in os.environ:
                    del os.environ[var]

            try:
                # Test with no environment variables
                config = _load_mail_config_from_env()
                assert config.mail_configured is False

                # Test with partial environment variables
                os.environ["MAIL_SERVER"] = "smtp.test.com"
                os.environ["MAIL_PORT"] = "587"
                # Missing USERNAME and PASSWORD
                config = _load_mail_config_from_env()
                assert config.mail_configured is False

            finally:
                # Restore original environment
                for var, value in original_values.items():
                    if value is not None:
                        os.environ[var] = value
                    elif var in os.environ:
                        del os.environ[var]

    def test_mail_send_threaded_email_exception(self, lms_application):
        """Test send_threaded_email when mail sending fails."""
        from now_lms.mail import send_threaded_email
        from flask_mail import Mail, Message

        with lms_application.app_context():
            # Create mock mail object that raises exception
            mock_mail = Mock(spec=Mail)
            mock_mail.send.side_effect = Exception("SMTP connection failed")

            # Create test message
            msg = Message(subject="Test Subject", recipients=["test@example.com"], body="Test message")

            # Should handle exception gracefully
            send_threaded_email(lms_application, mock_mail, msg, "test log", "test flash")
            mock_mail.send.assert_called_once_with(msg)

    def test_misc_concatenar_parametros_a_url_edge_cases(self):
        """Test concatenar_parametros_a_url with edge cases."""
        from now_lms.misc import concatenar_parametros_a_url

        # Test with all None parameters
        result = concatenar_parametros_a_url(None, None, None, "")
        assert result == ""

        # Test with empty values - function skips empty arg/val pairs
        result = concatenar_parametros_a_url(None, "", "", "?")
        assert result == "?"

    def test_misc_markdown_to_clean_html_malicious_content(self):
        """Test markdown_to_clean_html with potentially malicious content."""
        from now_lms.misc import markdown_to_clean_html

        # Test with script tags (should be cleaned)
        malicious_text = "Normal text <script>alert('xss')</script> more text"
        result = markdown_to_clean_html(malicious_text)
        assert "<script>" not in result
        assert "Normal text" in result
        assert "more text" in result

    def test_misc_sanitize_slide_content_malicious_content(self):
        """Test sanitize_slide_content with malicious content."""
        from now_lms.misc import sanitize_slide_content

        # Test with script and iframe tags (should be removed)
        malicious_html = '<p>Safe content</p><script>alert("xss")</script><iframe src="evil.com"></iframe>'
        result = sanitize_slide_content(malicious_html)

        assert "<p>Safe content</p>" in result
        assert "<script>" not in result
        assert "<iframe>" not in result
