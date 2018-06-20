"""
A command-line utility for fetching Parameter Store parameters via the AWS CLI.

Allows the names, types and values of all parameters matching a given name filter to be collected.

Usage:

    Provide:

        <name-prefix> - The string by which to filter parameters

        OPTIONAL:
        -o <output-file> - Filename with path indicating a file in which to store the fetched
                           parameters

    Returns an array containing the names, types and values of all parameters with names beginning
    with 'name-prefix'.

    If an output path is not provided, any results are written to stdout.
"""


import argparse
import json
import sys

from itertools import zip_longest
from subprocess import run, PIPE


class NonZeroErrorCode(Exception):
    pass


class NoParametersFound(Exception):
    pass


class InvalidPathError(Exception):
    pass


def grouper(iterable, n, fillvalue=None):
    """Collect data into fixed-length chunks or blocks"""
    # grouper('ABCDEFG', 3, 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


class BaseCommand:

    @property
    def call_args(self):
        raise NotImplementedError("Implemented via subclasses.")

    def __call__(self):
        """Run the command."""
        completed_process = run(self.call_args, stdout=PIPE)
        if completed_process.returncode != 0:
            raise NonZeroErrorCode(completed_process.returncode)
        return json.loads(completed_process.stdout.decode())


class DescribeParameters(BaseCommand):
    """An object representing a single 'aws ssm describe-parameters' command."""

    base_command = "aws ssm describe-parameters"

    filters_arg = "--filters"
    filters_value = "Key=Name,Values={name_prefix}"

    next_arg = "--next-token"

    def __init__(self, name_prefix=None, next_token=None):
        self.name_prefix = name_prefix
        self.next_token = next_token

    @property
    def call_args(self):
        args = self.base_command.split(" ")
        if self.name_prefix:
            args.append(self.filters_arg)
            args.append(self.filters_value.format(name_prefix=self.name_prefix))
        if self.next_token:
            args.append(self.next_arg)
            args.append(self.next_token)
        return args


class GetParameters(BaseCommand):

    base_command = "aws ssm get-parameters"

    names_arg = "--names"
    decryption_arg = "--with-decryption"

    max_length = 10

    def __init__(self, names=None):
        self.names = names or []
        if not self.names:
            raise AssertionError("One or more parameter names must be provided.")
        elif len(self.names) > self.max_length:
            raise AssertionError("Can't request more than {} parameters at once.".format(self.max_length))

    @property
    def call_args(self):
        args = self.base_command.split(" ")
        args.append(self.names_arg)
        args.extend(self.names)
        args.append(self.decryption_arg)
        return args


class CompileParameters:

    parameters_key = "Parameters"
    next_token_key = "NextToken"

    parameter_name_key = "Name"

    def __init__(self, name_prefix):
        self.name_prefix = name_prefix

    def _get_names(self):
        parameters = []
        first_page = DescribeParameters(self.name_prefix)()
        parameters.extend(first_page.get(self.parameters_key, []))
        next_token = first_page.get(self.next_token_key, None)
        while next_token:
            results = DescribeParameters(self.name_prefix, next_token)()
            parameters.extend(results.get(self.parameters_key))
            next_token = results.get(self.next_token_key, None)
        if not parameters:
            msg = "No Parameters found for name prefix: {}".format(self.name_prefix)
            raise NoParametersFound(msg)
        return [parameter.get(self.parameter_name_key) for parameter in parameters]

    def _get_values(self, names):
        parameters = []
        for names_subset in grouper(names, GetParameters.max_length):
            results = GetParameters([name for name in names_subset if name])()
            parameters.extend(results.get(self.parameters_key))
        return parameters

    def __call__(self):
        names = self._get_names()
        return self._get_values(names)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Fetch parameters from AWS Parameter Store')
    parser.add_argument('prefix', type=str)

    args = parser.parse_args()

    commands = CompileParameters(args.prefix)
    try:
        parameters = commands()
    except (NonZeroErrorCode, NoParametersFound) as error:
        print(repr(error))
        sys.exit(1)

    print(json.dumps(parameters, indent=4))
