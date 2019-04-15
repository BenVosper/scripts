from os.path import join
from unittest import TestCase
from unittest.mock import patch

from git.comp import main


class TestComp(TestCase):

    repos_dict = {
        "install_directory": "foo",
        "repos": [
            {
                "directory_name": "bar"
            },
            {
                "directory_name": "baz"
            }
        ]
    }

    @patch("git.comp.argparse")
    @patch("git.comp.chdir")
    @patch("git.comp.parse_settings", return_value=repos_dict)
    @patch("git.comp.repo_is_clean", side_effect=[False, True])
    @patch("git.comp.update_master")
    def test_main(self, mock_update, _, __, mock_chdir, ___):
        main()

        self.assertEqual(mock_chdir.call_count, 2)
        first_chdir, second_chdir = mock_chdir.call_args_list
        self.assertEqual(first_chdir[0][0], join("foo", "bar"))
        self.assertEqual(second_chdir[0][0], join("foo", "baz"))

        self.assertEqual(mock_update.call_count, 1)
