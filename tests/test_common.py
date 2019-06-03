import json

from functools import wraps
from subprocess import PIPE
from unittest import TestCase
from unittest.mock import patch, Mock, PropertyMock, call

from common import BaseCommand, BasePaginatedCommand, NonZeroErrorCode


def get_mock_response(return_code, response_bytes):
    mock_response = Mock()
    type(mock_response).returncode = PropertyMock(return_value=return_code)
    type(mock_response).stdout = PropertyMock(return_value=response_bytes)
    return mock_response


def patch_run(return_code=0, json_bytes_response=None):
    json_bytes_response = json_bytes_response or json.dumps({}).encode()

    def decorator(func):
        mock_response = get_mock_response(return_code, json_bytes_response)

        @wraps(func)
        @patch("common.run", return_value=mock_response)
        def patched(*args, **kwargs):
            func(*args, **kwargs)
        return patched
    return decorator


def patch_command(command_class, response):
    """Patch calls to 'command_class'.

    Successive calls can be emulated by passing 'response' as a list.
    """
    if not isinstance(response, list):
        response = [response]

    def decorator(func):
        @wraps(func)
        @patch.object(command_class, "__call__", side_effect=response)
        @patch.object(command_class, "__init__", return_value=None)
        def patched(*args, **kwargs):
            func(*args, **kwargs)
        return patched
    return decorator


class TestBaseCommand(TestCase):

    response_dict = {"foo": "bar"}
    json_bytes_response = json.dumps(response_dict).encode()

    @patch.object(BaseCommand, "call_args")
    @patch_run(return_code=0, json_bytes_response=json_bytes_response)
    def test_call(self, mock_run, mock_call_args):
        """Calling the command calls 'run' with 'call_args'."""
        response = BaseCommand()()
        self.assertEqual(response, self.response_dict)
        self.assertEqual(mock_run.call_args_list, [call(mock_call_args, stdout=PIPE)])

    @patch.object(BaseCommand, "call_args")
    @patch_run(return_code=1, json_bytes_response=json_bytes_response)
    def test_call_error(self, mock_run, _):
        """Calling the command raises an error if 'run' returns a non-zero error code."""
        self.assertRaisesRegex(
            NonZeroErrorCode,
            "1",
            BaseCommand()
        )


class TestBasePaginatedCommand(TestCase):

    class DummyPaginatedCommand(BasePaginatedCommand):

        base_command = "foo"

        next_arg = "next"
        results_key = "results"

    page_one = {
        "results": [0, 1],
        "next": "/page/two"
    }

    page_two = {
        "results": [2]
    }

    pages = [json.dumps(page).encode() for page in (page_one, page_two)]

    @patch_run(json_bytes_response=pages[1])
    def test_one_page(self, _):
        results = self.DummyPaginatedCommand().get_all()

        self.assertEqual(results, [2])

    @patch(
        "common.run",
        side_effect=[get_mock_response(0, response_bytes) for response_bytes in pages]
    )
    def test_two_pages(self, _):
        results = self.DummyPaginatedCommand.get_all()

        self.assertEqual(results, [0, 1, 2])
