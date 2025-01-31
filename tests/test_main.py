import re
from unittest.mock import MagicMock, patch

import pytest
import requests

from slack_webhook_notifier.main import send_slack_message, slack_notify

# Constants for testing
TEST_WEBHOOK_URL = "https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXXXXXXXXXXXXXXXX"
TEST_FUNC_IDENTIFIER = "test_func"
TEST_USER_ID = "U123456"
TEST_ERROR_MESSAGE = "Test error"


def sample_function_success():
    return "Success!"


def sample_function_failure():
    raise ValueError(TEST_ERROR_MESSAGE)


@pytest.fixture
def mock_requests_post():
    """Mocks the requests.post method for Slack notifications."""
    with patch("requests.post") as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        yield mock_post


def test_send_slack_message_success(mock_requests_post):
    """Tests successful Slack message sending."""
    message = "Test Slack message"
    send_slack_message(TEST_WEBHOOK_URL, message)

    mock_requests_post.assert_called_once_with(TEST_WEBHOOK_URL, json={"text": message}, timeout=10)


def test_send_slack_message_failure(mock_requests_post):
    """Tests Slack message sending failure."""
    mock_requests_post.side_effect = requests.exceptions.RequestException("Slack error")

    with pytest.raises(requests.exceptions.RequestException, match="Slack error"):
        send_slack_message(TEST_WEBHOOK_URL, "Test failure message")


def test_slack_notify_decorator_success(mock_requests_post):
    """Tests Slack notifications for successful function execution."""

    @slack_notify(TEST_WEBHOOK_URL, TEST_FUNC_IDENTIFIER, TEST_USER_ID)
    def test_func():
        return sample_function_success()

    result = test_func()

    assert result == "Success!"
    assert mock_requests_post.call_count == 2

    actual_calls = [args[1]["json"]["text"] for args in mock_requests_post.call_args_list]

    assert any(
        re.search(r"Automation has started\.\nStart Time: .*?\nFunction Caller: test_func", msg) for msg in actual_calls
    )
    assert any(
        re.search(
            r"Automation has completed successfully\.\nStart Time: .*?\nEnd Time: .*?\nDuration: .*?\nFunction Caller: test_func",
            msg,
        )
        for msg in actual_calls
    )


def test_slack_notify_decorator_failure(mock_requests_post):
    """Tests Slack notifications when a function raises an exception."""

    @slack_notify(TEST_WEBHOOK_URL, TEST_FUNC_IDENTIFIER, TEST_USER_ID)
    def test_func():
        return sample_function_failure()

    with pytest.raises(ValueError, match=TEST_ERROR_MESSAGE):
        test_func()

    assert mock_requests_post.call_count == 2

    actual_calls = [args[1]["json"]["text"] for args in mock_requests_post.call_args_list]

    assert any(
        re.search(r"Automation has started\.\nStart Time: .*?\nFunction Caller: test_func", msg) for msg in actual_calls
    )
    assert any(
        re.search(
            r"<@U123456>\s+Automation has crashed\.\nStart Time: .*?\nEnd Time: .*?\nDuration: .*?\nFunction Caller: test_func\nError: Test error",
            msg,
        )
        for msg in actual_calls
    )


def test_slack_notify_decorator_sql_error_cleaning(mock_requests_post):
    """Tests that long SQL statements are removed from error messages."""

    sql_error_message = (
        "[SQL: INSERT INTO table (column) VALUES ('bad_data')]\n"
        "(psycopg2.errors.InvalidDatetimeFormat) invalid input syntax for type timestamp: 'Pending'"
    )

    @slack_notify(TEST_WEBHOOK_URL, TEST_FUNC_IDENTIFIER, TEST_USER_ID)
    def test_func():
        raise ValueError(sql_error_message)

    with pytest.raises(ValueError, match="invalid input syntax for type timestamp: 'Pending'"):
        test_func()

    assert mock_requests_post.call_count == 2

    actual_calls = [args[1]["json"]["text"] for args in mock_requests_post.call_args_list]

    # Ensure that the SQL statement is removed from the error message
    assert any(
        re.search(
            r"Automation has crashed\.\nStart Time: .*?\nEnd Time: .*?\nDuration: .*?\nFunction Caller: test_func\nError: \(psycopg2.errors.InvalidDatetimeFormat\) invalid input syntax for type timestamp: 'Pending'",
            msg,
        )
        for msg in actual_calls
    )
