import json

from unittest import TestCase
from unittest.mock import patch, Mock

from git.bootstrap_repos import install_python_dependencies, get_existing_conda_envs


class TestBootstrapRepos(TestCase):

    @patch("git.bootstrap_repos.run")
    def test_install_python_dependencies(self, mock_run):
        install_python_dependencies("conda activate", "foo", "pip install", "conda deactivate")

        mock_run.assert_called_once_with(
            "conda activate foo && pip install && conda deactivate",
            check=True,
            shell=True
        )

    def test_get_existing_conda_envs(self):
        env_paths = ["foo/bar/baz", "this/that", "bong"]
        conda_list_result = json.dumps({"envs": env_paths})

        with patch("git.bootstrap_repos.run", return_value=Mock(stdout=conda_list_result)):
            existing_envs = get_existing_conda_envs("conda env list --json")

        self.assertListEqual(existing_envs, ["baz", "that", "bong"])
