from unittest.mock import call, patch

import pytest
from freezegun import freeze_time

from slack_webhook_notifier.main import send_slack_message, slack_notify


@pytest.fixture
def webhook_url():
    return "https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX"


@freeze_time("2025-01-21 23:36:28")
def test_send_slack_message_success(webhook_url):
    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        send_slack_message(webhook_url, "Test message")
        mock_post.assert_called_once_with(webhook_url, json={"text": "Test message"}, timeout=10)


@freeze_time("2025-01-21 23:36:28")
def test_send_slack_message_failure(webhook_url):
    with patch("requests.post") as mock_post:
        mock_post.side_effect = Exception("Request failed")
        with pytest.raises(Exception, match="Request failed"):
            send_slack_message(webhook_url, "Test message")


@freeze_time("2025-01-21 23:36:28")
def test_slack_notify_decorator_success(webhook_url):
    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 200

        @slack_notify(webhook_url, "test_func")
        def test_func():
            return "success"

        result = test_func()
        assert result == "success"
        assert mock_post.call_count == 2
        start_time = "2025-01-21 23:36:28"
        end_time = "2025-01-21 23:36:28"
        expected_calls = [
            call(
                webhook_url,
                json={"text": f"Automation has started.\nStart Time: {start_time}\nFunction Caller: test_func"},
                timeout=10,
            ),
            call(
                webhook_url,
                json={
                    "text": f"Automation has completed successfully.\n"
                    f"Start Time: {start_time}\n"
                    f"End Time: {end_time}\n"
                    f"Duration: 0:00:00\n"
                    f"Function Caller: test_func"
                },
                timeout=10,
            ),
        ]
        mock_post.assert_has_calls(expected_calls, any_order=True)


@freeze_time("2025-01-21 23:36:28")
def test_slack_notify_decorator_failure(webhook_url):
    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 200

        @slack_notify(webhook_url, "test_func", user_id="U123456")
        def test_func():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            test_func()
        assert mock_post.call_count == 2
        start_time = "2025-01-21 23:36:28"
        end_time = "2025-01-21 23:36:28"
        expected_calls = [
            call(
                webhook_url,
                json={"text": f"Automation has started.\nStart Time: {start_time}\nunction Caller: test_func"},
                timeout=10,
            ),
            call(
                webhook_url,
                json={
                    "text": f"Automation has crashed.\n"
                    f"Start Time: {start_time}\n"
                    f"End Time: {end_time}\n"
                    f"Duration: 0:00:00\n"
                    f"Function Caller: test_func\n"
                    f"Error: Test error\n"
                    f"<@U123456> "
                },
                timeout=10,
            ),
        ]
        mock_post.assert_has_calls(expected_calls, any_order=True)
