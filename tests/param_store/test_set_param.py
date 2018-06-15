import json

from io import StringIO
from functools import wraps
from unittest import TestCase
from unittest.mock import patch

from param_store.set_param import PutParameter, run_commands


class TestPutParameter(TestCase):

    parameter_name = "foo"
    parameter_value = "bar"

    def test_invalid_type(self):
        """An error is raised when an invalid parameter type is given."""
        self.assertRaisesRegex(
            RuntimeError,
            "Invalid parameter type",
            PutParameter,
            "",
            "",
            "BAD"
        )

    def test_cli_input_json(self):
        """The 'cli-input-json' string is correctly formatted."""
        expected_string = ("{\"Name\": \"foo\", "
                           "\"Value\": \"bar\", "
                           "\"Type\": \"SecureString\", "
                           "\"Overwrite\": false}")
        self.assertEqual(PutParameter(self.parameter_name, self.parameter_value).cli_input_json,
                         expected_string)

    def test_value_is_url(self):
        """Values that are valid URLs are detected correctly."""
        self.assertTrue(PutParameter(self.parameter_name, "http://example.com").value_is_url)
        self.assertTrue(PutParameter(self.parameter_name, "http://example.com/path").value_is_url)
        self.assertFalse(PutParameter(self.parameter_name, "example.com").value_is_url)
        self.assertFalse(PutParameter(self.parameter_name, "foo").value_is_url)

    def test_call_args(self):
        """Call args are compiled correctly."""
        command = PutParameter(self.parameter_name, self.parameter_value)
        self.assertListEqual(
            command.call_args,
            [
                "aws", "ssm", "put-parameter",
                "--name", self.parameter_name,
                "--value", self.parameter_value,
                "--type", "SecureString",
                "--no-overwrite"
            ]
        )

    def test_call_args_overwrite_true(self):
        """The 'overwrite' flag is respected when compiling call args."""
        command = PutParameter(self.parameter_name, self.parameter_value, overwrite=True)
        self.assertListEqual(
            command.call_args,
            [
                "aws", "ssm", "put-parameter",
                "--name", self.parameter_name,
                "--value", self.parameter_value,
                "--type", "SecureString",
                "--overwrite"
            ]
        )

    def test_call_args_url(self):
        """Call args are compiled correctly for a URL value."""
        command = PutParameter(self.parameter_name,  "http://example.com")
        self.assertListEqual(
            command.call_args,
            [
                "aws", "ssm", "put-parameter",
                "--cli-input-json",
                command.cli_input_json
            ]
        )

    @patch("param_store.set_param.set_param.call")
    def test_call(self, mock_call):
        """Calling the command calls 'subprocess.call' with correct args."""
        command = PutParameter(self.parameter_name, self.parameter_value)
        args = command.call_args
        command()
        mock_call.assert_called_once_with(args)

    def test_from_dict(self):
        """A 'PutParameter' object is created from a correctly formatted JSON input."""
        command_parameters = {
            "Name": self.parameter_name,
            "Value": self.parameter_value,
            "Type": PutParameter.ParameterTypes.STRINGLIST,
            "Overwrite": True
        }
        command = PutParameter.from_dict(command_parameters)
        self.assertEqual(command.parameter, self.parameter_name)
        self.assertEqual(command.value, self.parameter_value)
        self.assertEqual(command.type, PutParameter.ParameterTypes.STRINGLIST)
        self.assertEqual(command.overwrite, True)

    def test_from_dict_defaults(self):
        """Objects created using 'from_dict' use default values for omitted keys."""
        command_parameters = {
            "Name": self.parameter_name,
            "Value": self.parameter_value
        }
        command = PutParameter.from_dict(command_parameters)
        self.assertEqual(command.parameter, self.parameter_name)
        self.assertEqual(command.value, self.parameter_value)
        self.assertEqual(command.type, PutParameter.ParameterTypes.SECURESTRING)
        self.assertEqual(command.overwrite, False)


def patch_command(func):
    @wraps(func)
    @patch.object(PutParameter, "__init__", return_value=None)
    @patch.object(PutParameter, "__call__")
    def patched(*args, **kwargs):
        func(*args, **kwargs)
    return patched


class TestRunCommands(TestCase):

    parameter_args = ("foo", "bar", "baz", True)

    def _json_file_object(self, obj):
        return StringIO(json.dumps(obj))

    @patch_command
    def test_single_parameter(self, mock_call, mock_init):
        """Individual arguments result in a single call."""
        run_commands(*self.parameter_args)
        mock_init.assert_called_once_with(*self.parameter_args)
        mock_call.assert_called_once_with()

    def test_invalid_json(self):
        """JSON input missing required keys raises an error."""
        input_json = self._json_file_object([{"this": "that"}])
        self.assertRaisesRegex(
            RuntimeError,
            "commands missing",
            run_commands,
            *self.parameter_args,
            input_json
        )

    @patch_command
    def test_json_single_parameter(self, mock_call, mock_init):
        """JSON input with a single valid parameter results in a single call."""
        input_json = self._json_file_object([
            {"Name": "A", "Value": "1"}
        ])
        run_commands(*self.parameter_args, input_json)
        mock_init.assert_called_once_with(parameter="A", value="1", type="baz", overwrite=True)
        mock_call.assert_called_once_with()

    @patch_command
    def test_json_multiple_parameters(self, mock_call, mock_init):
        """JSON input with multiple valid parameters results in multiple calls."""
        input_json = self._json_file_object([
            {"Name": "A", "Value": "1"},
            {"Name": "B", "Value": "2", "Type": "3", "Overwrite": False}
        ])
        run_commands(*self.parameter_args, input_json)
        self.assertListEqual(mock_init.call_args_list, [
            ({"parameter": "A", "value": "1", "type": "baz", "overwrite": True},),
            ({"parameter": "B", "value": "2", "type": "3", "overwrite": False},)
        ])
        self.assertEqual(mock_init.call_count, 2)
