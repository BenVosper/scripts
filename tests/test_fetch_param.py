from unittest import TestCase
from unittest.mock import patch, call

from tests.test_common import patch_command
from aws.fetch_params import (
    grouper, DescribeParameters, GetParameters, CompileParameters, NoParametersFound
)


class TestGrouper(TestCase):

    def test_grouper(self):
        """Iterables are grouped as expected."""
        self.assertListEqual(
            [*grouper("12345678", 3)], [("1", "2", "3"), ("4", "5", "6"), ("7", "8", None)]
        )
        self.assertListEqual(
            [*grouper("123", 2, "X")], [("1", "2"), ("3", "X")]
        )
        self.assertListEqual(
            [*grouper("", 2)], []
        )


class TestDescribeParameters(TestCase):

    name_prefix = "foo"
    next_token = "bar"

    def test_call_args_initial(self):
        """Initial 'call_args' are formatted as expected."""
        command = DescribeParameters(self.name_prefix)
        self.assertEqual(
            command.call_args,
            [*command.base_command.split(" "), command.filters_arg, "Key=Name,Values=foo"]
        )

    def test_call_args_next(self):
        """'call_args' with the 'next_token' are formatted as expected."""
        command = DescribeParameters(self.name_prefix, self.next_token)
        self.assertEqual(
            command.call_args,
            [
                *command.base_command.split(" "),
                command.filters_arg,
                "Key=Name,Values=foo",
                command.next_arg,
                self.next_token
            ]
        )


class TestGetParameters(TestCase):

    names = ["foo"]

    def test_no_parameters_error(self):
        """Initialising command with no parameter names raises an error."""
        self.assertRaisesRegex(
            AssertionError,
            "One or more parameter names must be provided",
            GetParameters
        )

    def test_too_many_parameters_error(self):
        """Initialising command with too many parameter names raises an error."""
        self.assertRaisesRegex(
            AssertionError,
            "Can't request more than 10 parameters at once",
            GetParameters,
            self.names * (GetParameters.max_length + 1)
        )

    def test_call_args(self):
        """Call args are formatted as expected."""
        command = GetParameters(self.names)
        self.assertEqual(
            command.call_args,
            [
                *command.base_command.split(" "),
                command.names_arg,
                self.names[0],
                command.decryption_arg
            ]
        )


def _get_describe_parameters_response(names, next_token=None):
    """Construct the expected response from a call to 'DescribeParameters'."""
    response = {
        CompileParameters.parameters_key: [
            {CompileParameters.parameter_name_key: name} for name in names
        ]
    }
    if next_token:
        response[CompileParameters.next_token_key] = next_token
    return response


def _get_get_parameters_response(parameters):
    """Construct the expected response from a call to 'GetParameters'."""
    return {CompileParameters.parameters_key: [{"Name": key, "Value": value}
                                               for key, value in parameters.items()]}


class TestCompileParameters(TestCase):

    name_prefix = "foo"
    names = ["foo_bar", "foo_bang"]
    next_token = "next"

    parameters = {names[0]: 1, names[1]: 2}

    @patch_command(DescribeParameters, _get_describe_parameters_response([]))
    def test_get_names_error(self, _, __):
        """Calling '_get_names' raises an error if no parameters are found."""
        self.assertRaisesRegex(
            NoParametersFound,
            "No Parameters found for name prefix",
            CompileParameters(self.name_prefix)._get_names
        )

    @patch_command(DescribeParameters, _get_describe_parameters_response([names[0]]))
    def test_get_names(self, mock_command_init, mock_command_call):
        """Calling '_get_names' fetches parameter names as expected."""
        names = CompileParameters(self.name_prefix)._get_names()
        self.assertEqual(names, [self.names[0]])
        mock_command_init.assert_called_once_with(self.name_prefix)
        mock_command_call.assert_called_once_with()

    @patch_command(DescribeParameters, [_get_describe_parameters_response([names[0]], next_token),
                                        _get_describe_parameters_response([names[1]])])
    def test_get_names_multiple_pages(self, mock_command_init, mock_command_call):
        """Calling '_get_names' fetches parameter names from multiple pages as expected."""
        names = CompileParameters(self.name_prefix)._get_names()
        self.assertEqual(names, [self.names[0], "foo_bang"])
        self.assertEqual(
            mock_command_init.call_args_list,
            [call(self.name_prefix), call(self.name_prefix, self.next_token)]
        )
        self.assertEqual(
            mock_command_call.call_args_list,
            [call(), call()]
        )

    @patch_command(GetParameters, _get_get_parameters_response(parameters))
    def test_get_values(self, mock_command_init, mock_command_call):
        """Calling '_get_values' extracts parameter dicts as expected."""
        parameters = CompileParameters(self.name_prefix)._get_values(self.names)
        mock_command_init.assert_called_once_with(self.names)
        mock_command_call.assert_called_once_with()
        self.assertEqual(len(parameters), 2)
        for response_dict, (name, value) in zip(parameters, self.parameters.items()):
            self.assertEqual(response_dict["Name"], name)
            self.assertEqual(response_dict["Value"], value)

    @patch.object(CompileParameters, "_get_values")
    @patch.object(CompileParameters, "_get_names", return_value=names)
    def test_call(self, mock_get_names, mock_get_values):
        """Calling the 'CompileParameters' calls sub-commands and returns output."""
        parameters = CompileParameters(self.name_prefix)()
        self.assertEqual(parameters, mock_get_values.return_value)
        mock_get_names.assert_called_once_with()
        mock_get_values.assert_called_once_with(self.names)
