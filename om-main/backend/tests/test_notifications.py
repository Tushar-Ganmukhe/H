from app.agents.execution_agent import send_notification
from app.services.user_service import UserService
import os

def test_send_notification_no_credentials(monkeypatch):
    # ensure no exception when Twilio not configured
    # temporarily unset env vars
    monkeypatch.delenv("TWILIO_ACCOUNT_SID", raising=False)
    monkeypatch.delenv("TWILIO_AUTH_TOKEN", raising=False)
    monkeypatch.delenv("TWILIO_WHATSAPP_FROM", raising=False)
    # call with dummy phone
    send_notification("+1234567890", "Test message")
    # if we reach here without error, it's fine


def test_user_service_register_and_notify(tmp_path):
    # register a user and ensure user data persists
    # use tmp file for database by monkeypatching path
    monkeypatch = __import__('pytest').MonkeyPatch()
    monkeypatch.setattr('app.services.user_service.USERS_DB_FILE', str(tmp_path / 'users.json'))

    result = UserService.register_user('Notify', '555', None, 'pw', None, 'user')
    assert result['success']
    user = UserService.get_user(result['user']['id'])
    assert user['phone'] == '555'
    monkeypatch.undo()
