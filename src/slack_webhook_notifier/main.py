import re
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable, Optional

import requests


def slack_notify(
    webhook_url: str, func_identifier: str, user_id: Optional[str] = None
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time: datetime = datetime.now()
            start_message: str = (
                f"Automation has started.\n"
                f"Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"Function Caller: {func_identifier}"
            )
            send_slack_message(webhook_url, start_message)
            try:
                result = func(*args, **kwargs)
                end_time: datetime = datetime.now()
                duration: timedelta = end_time - start_time
                end_message: str = (
                    f"Automation has completed successfully.\n"
                    f"Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"Duration: {duration!s}\n"
                    f"Function Caller: {func_identifier}"
                )
                send_slack_message(webhook_url, end_message)
                return result
            except Exception as err:
                end_time = datetime.now()
                duration = end_time - start_time

                # Remove any large SQL query from error message if it's a SQLAlchemy error
                error_message = str(err)
                if "SQL: " in error_message:
                    try:
                        error_message = re.sub(r"\[SQL: .*?\]", "", error_message).strip()
                    except Exception as e:
                        raise e

                user_mention: str = f"<@{user_id}> " if user_id else ""
                error_message: str = (
                    f"{user_mention}\n"
                    f"Automation has crashed.\n"
                    f"Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"Duration: {duration!s}\n"
                    f"Function Caller: {func_identifier}\n"
                    f"Error: {error_message!s}"
                )
                send_slack_message(webhook_url, error_message)
                raise err

        return wrapper

    return decorator


def send_slack_message(webhook_url: str, message: str) -> None:
    try:
        response = requests.post(webhook_url, json={"text": message}, timeout=10)
        response.raise_for_status()  # Raises HTTPError if status code is 4xx/5xx
    except requests.exceptions.RequestException as e:
        print(f"Failed to send Slack notification: {e}")
        raise  # Ensure exceptions are raised for testing purposes
