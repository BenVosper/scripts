import json

from subprocess import run, PIPE


class NonZeroErrorCode(Exception):
    pass


class BaseCommand:

    base_command = None

    @property
    def call_args(self):
        return self.base_command.split(" ")

    def __call__(self):
        """Run the command."""
        completed_process = run(self.call_args, stdout=PIPE)
        if completed_process.returncode != 0:
            raise NonZeroErrorCode(completed_process.returncode)
        return json.loads(completed_process.stdout.decode())


class BasePaginatedCommand(BaseCommand):

    next_arg = None
    results_key = None

    def __init__(self, next_token=None):
        self.next_token = next_token

    @property
    def call_args(self):
        args = super().call_args
        if self.next_token:
            args += [self.next_arg, self.next_token]
        return args

    @classmethod
    def get_all(cls, *args, **kwargs):
        results = []
        first_page = cls(*args, **kwargs)()
        results.extend(first_page[cls.results_key])
        next_token = first_page.get(cls.next_arg, None)
        while next_token:
            page = cls(*args, **kwargs, next_token=next_token)()
            results.extend(page[cls.results_key])
            next_token = page.get("next_token", None)
        return results
