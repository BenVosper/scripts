"""
A command-line utility that allows the creation and updating of Parameter Store parameters
via the AWS CLI.

Allows multiple parameters to be updated with one command. Since parameter names and values can be
written and checked in a text-editor, the likelihood of errors resulting from typos and mis-clicks
in the AWS UI is reduced.

You must have successfully run 'aws configure' before using this tool.

Usage:

    Provide either:

        -p <parameter-name>
        -v <parameter-value>

        OPTIONAL:
        -t <value-type> "String" / "StringList" / "SecureString". Defaults to "SecureString"
        -o Flag indicating that parameter should be overwritten

    OR:

        -j <path-to-json-file>

        The JSON file should contain an array with one or more dicts of the following format.
        (Format is based on the '--cli-input-json' argument for the AWS 'put-parameter' command.)

        {
            "Name": <parameter-name>,
            "Value": <parameter-value>,
            "Type": <value-type>              // OPTIONAL. Defaults to "SecureString"
            "Overwrite: <boolean>             // OPTIONAL. Defaults to False
        }

        If "type" or "overwrite" are omitted, they default to the values set by the
        -t and -o flags.

        All special characters in values must be appropriately escaped.
"""

import argparse
import json

from subprocess import call


class PutParameter:
    """An object representing a single 'aws ssm put-parameter' command.

    We use the '--cli-input-json' argument of the command to avoid issues with using URLs as
    values. The (questionably useful) default behaviour of 'ssm put-parameter' is to perform a GET
    on valid URLs and use the response as the value.
    """

    class ParameterTypes:
        STRING = "String"
        STRINGLIST = "StringList"
        SECURESTRING = "SecureString"

    base_command = "aws ssm put-parameter"

    cli_input_json_arg = "--cli-input-json"

    def __init__(self, parameter, value, type=ParameterTypes.SECURESTRING, overwrite=False):
        self.parameter = parameter
        self.value = value
        self.type = type
        self.overwrite = overwrite

        types = [self.ParameterTypes.STRING, self.ParameterTypes.SECURESTRING, self.ParameterTypes.STRINGLIST]
        if self.type not in types:
            msg = ("Invalid parameter type: {}. Specify one of: {}".format(
                self.type, ", ".join(types)))
            raise RuntimeError(msg)

    @property
    def cli_input_json(self):
        parameter_dict = {
            "Name": self.parameter,
            "Value": self.value,
            "Type": self.type,
            "Overwrite": self.overwrite
        }
        return json.dumps(parameter_dict)

    @property
    def call_args(self):
        args = self.base_command.split(" ")
        args.append(self.cli_input_json_arg)
        args.append(self.cli_input_json)
        return args

    def __call__(self):
        """Run the command."""
        return call(self.call_args)

    @classmethod
    def from_dict(cls, command_parameters):
        """Create an instance from a dict of the '--cli-input-json' format."""
        if not {"Name", "Value"}.issubset(command_parameters.keys()):
            raise RuntimeError("One or more commands missing 'Name' and/or 'Value' keys.")
        optional = {arg: command_parameters[key] for arg, key in
                    (("type", "Type"), ("overwrite", "Overwrite")) if key in command_parameters}
        return cls(parameter=command_parameters["Name"],
                   value=command_parameters["Value"],
                   **optional)


def run_commands(parameter, value, parameter_type, overwrite, input_json=None):
    commands = []
    if input_json:
        commands_json = json.loads(input_json.read())
        for command_dict in commands_json:
            commands.append(
                PutParameter.from_dict({
                    "Type": parameter_type,
                    "Overwrite": overwrite,
                    **command_dict
                }))
    else:
        commands.append(
            PutParameter(
                parameter,
                value,
                parameter_type,
                overwrite
            )
        )

    for command in commands:
        return_code = command()
        if return_code == 0:
            print("Success! {} = {}".format(command.parameter, command.value))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Upload parameters to AWS Parameter Store')
    parser.add_argument('-p', '--parameter', default="", type=str)
    parser.add_argument('-v', '--value', default="", type=str)
    parser.add_argument('-t', '--type', default=PutParameter.ParameterTypes.SECURESTRING, type=str)
    parser.add_argument('-o', '--overwrite', action="store_true", help="Overwrite existing parameter")
    parser.add_argument('-j', '--json', nargs="?", type=argparse.FileType('r'))

    args = parser.parse_args()

    run_commands(
        args.parameter,
        args.value,
        args.type,
        args.overwrite,
        args.json
    )
