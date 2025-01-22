import time
from unittest.mock import MagicMock, patch

import pytest

from slack_webhook_notifier.main import send_slack_message, slack_notify


def test_slack_notify_success():
    webhook_url = "https://hooks.slack.com/services/test"
    func_identifier = "test_function"
    user_id = "U12345678"

    @slack_notify(webhook_url, func_identifier, user_id)
    def sample_function():
        time.sleep(1)
        return "Success"

    with patch("slack_webhook_notifier.main.send_slack_message") as mock_send:
        result = sample_function()
        assert result == "Success"
        assert mock_send.call_count == 2
        start_call, end_call = mock_send.call_args_list
        assert "Automation has started" in start_call.args[1]
        assert "Automation has completed successfully" in end_call.args[1]


def test_slack_notify_failure():
    webhook_url = "https://hooks.slack.com/services/test"
    func_identifier = "test_function"
    user_id = "U12345678"

    @slack_notify(webhook_url, func_identifier, user_id)
    def failing_function():
        time.sleep(1)
        raise ValueError("Test error")

    with patch("slack_webhook_notifier.main.send_slack_message") as mock_send:
        with pytest.raises(ValueError, match="Test error"):
            failing_function()
        assert mock_send.call_count == 2
        start_call, error_call = mock_send.call_args_list
        assert "Automation has started" in start_call.args[1]
        assert "Automation has crashed" in error_call.args[1]
        assert "Test error" in error_call.args[1]


def test_send_slack_message():
    webhook_url = "https://hooks.slack.com/services/test"
    message = "Test message"
    with patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        send_slack_message(webhook_url, message)
        mock_post.assert_called_once_with(webhook_url, json={"text": message})
