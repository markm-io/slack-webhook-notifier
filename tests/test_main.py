from unittest.mock import MagicMock, call, patch

import pytest
import requests
from freezegun import freeze_time

from slack_webhook_notifier.main import send_slack_message, slack_notify


@pytest.fixture
def webhook_url():
    return "https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX"


@freeze_time("2025-01-21 23:36:28")
def test_send_slack_message_success(webhook_url):
    with patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        send_slack_message(webhook_url, "Test message")
        mock_post.assert_called_once_with(webhook_url, json={"text": "Test message"}, timeout=10)


@freeze_time("2025-01-21 23:36:28")
def test_send_slack_message_failure(webhook_url):
    with patch("requests.post") as mock_post:
        mock_post.side_effect = requests.exceptions.RequestException("Request failed")
        with pytest.raises(requests.exceptions.RequestException, match="Request failed"):
            send_slack_message(webhook_url, "Test message")


@freeze_time("2025-01-21 23:36:28")
def test_send_slack_message_invalid_url():
    invalid_url = "https://invalid-url"
    with patch("requests.post") as mock_post:
        mock_post.side_effect = requests.exceptions.InvalidURL("Invalid URL")
        with pytest.raises(requests.exceptions.InvalidURL, match="Invalid URL"):
            send_slack_message(invalid_url, "Test message")


@freeze_time("2025-01-21 23:36:28")
def test_send_slack_message_timeout(webhook_url):
    with patch("requests.post") as mock_post:
        mock_post.side_effect = requests.exceptions.Timeout("Request timed out")
        with pytest.raises(requests.exceptions.Timeout, match="Request timed out"):
            send_slack_message(webhook_url, "Test message")


@freeze_time("2025-01-21 23:36:28")
def test_slack_notify_decorator_success(webhook_url):
    with patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        @slack_notify(webhook_url, "test_func")
        def test_func():
            return "success"

        result = test_func()
        assert result == "success"
        assert mock_post.call_count == 2
        expected_calls = [
            call(
                webhook_url,
                json={"text": "Automation has started.\nStart Time: 2025-01-21 23:36:28\nFunction Caller: test_func"},
                timeout=10,
            ),
            call(
                webhook_url,
                json={
                    "text": "Automation has completed successfully.\n"
                    "Start Time: 2025-01-21 23:36:28\n"
                    "End Time: 2025-01-21 23:36:28\n"
                    "Duration: 0:00:00\n"
                    "Function Caller: test_func"
                },
                timeout=10,
            ),
        ]
        mock_post.assert_has_calls(expected_calls, any_order=True)


@freeze_time("2025-01-21 23:36:28")
def test_slack_notify_decorator_failure(webhook_url):
    with patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        @slack_notify(webhook_url, "test_func", user_id="U123456")
        def test_func():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            test_func()

        assert mock_post.call_count == 2

        expected_calls = [
            call(
                webhook_url,
                json={"text": "Automation has started.\nStart Time: 2025-01-21 23:36:28\nFunction Caller: test_func"},
                timeout=10,
            ),
            call(
                webhook_url,
                json={
                    "text": "<@U123456> \n"
                    "Automation has crashed.\n"
                    "Start Time: 2025-01-21 23:36:28\n"
                    "End Time: 2025-01-21 23:36:28\n"
                    "Duration: 0:00:00\n"
                    "Function Caller: test_func\n"
                    "Error: Test error"
                },
                timeout=10,
            ),
        ]

        mock_post.assert_has_calls(expected_calls, any_order=True)
