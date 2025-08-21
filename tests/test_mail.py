from flask_mail import Mail, Message
from unittest.mock import MagicMock


def test_send_threaded_email_success(session_basic_db_setup):
    # Preparamos mocks
    mail = MagicMock(spec=Mail)
    msg = MagicMock(spec=Message)
    msg.recipients = ["test@example.com"]

    with session_basic_db_setup.app_context():
        from now_lms.mail import send_threaded_email

        # Ejecutamos la función
        send_threaded_email(session_basic_db_setup, mail, msg, _log="correo enviado", _flush="OK")

        # Verificamos que se envió el mensaje
        mail.send.assert_called_once_with(msg)
