from unittest import TestCase
from unittest.mock import call

from tests.test_common import patch_run

from aws.get_ecs_url import (
    NoResourceFound, ListClusters, ListServices, ListTasks, DescribeTasks,
    DescribeContainerInstances, DescribeEc2Instances, match_arn
)


class TestCommandArgs(TestCase):

    @patch_run()
    def test_list_clusters(self, mock_run):
        ListClusters()()

        expected_call_args = ["aws", "ecs", "list-clusters"]

        self.assertEqual(
            mock_run.call_args_list,
            [call(expected_call_args, stdout=-1)]
        )

    @patch_run()
    def test_list_services(self, mock_run):
        ListServices(cluster_arn="foo")()

        expected_call_args = ["aws", "ecs", "list-services", "--cluster", "foo"]

        self.assertEqual(
            mock_run.call_args_list,
            [call(expected_call_args, stdout=-1)]
        )

    @patch_run()
    def test_list_tasks(self, mock_run):
        ListTasks(cluster_arn="foo", service_arn="bar")()

        expected_call_args = [
            "aws", "ecs", "list-tasks", "--cluster", "foo",
            "--service", "bar", "--desired-status", "RUNNING"
        ]

        self.assertEqual(
            mock_run.call_args_list,
            [call(expected_call_args, stdout=-1)]
        )

    @patch_run()
    def test_describe_tasks(self, mock_run):
        DescribeTasks(cluster_arn="foo", task_arn="bar")()

        expected_call_args = [
            "aws", "ecs", "describe-tasks", "--cluster", "foo", "--tasks", "bar"
        ]

        self.assertEqual(
            mock_run.call_args_list,
            [call(expected_call_args, stdout=-1)]
        )

    @patch_run()
    def test_describe_container_instances(self, mock_run):
        DescribeContainerInstances(cluster_arn="foo", container_arn="bar")()

        expected_call_args = [
            "aws", "ecs", "describe-container-instances", "--cluster", "foo",
            "--container-instances", "bar"
        ]

        self.assertEqual(
            mock_run.call_args_list,
            [call(expected_call_args, stdout=-1)]
        )

    @patch_run()
    def test_describe_ec2_instances(self, mock_run):
        DescribeEc2Instances(instance_id="foo")()

        expected_call_args = [
            "aws", "ec2", "describe-instances", "--instance-ids", "foo"
        ]

        self.assertEqual(
            mock_run.call_args_list,
            [call(expected_call_args, stdout=-1)]
        )


class TestMatchArn(TestCase):

    def test_one_match(self):
        arns = ["12334/foo", "12121/bar", "1323/foe"]

        match = match_arn("foo", arns)

        self.assertEqual(match, arns[0])

    def test_multiple_matches(self):
        arns = ["12334/foo", "3313/foo", "1323/foe"]

        with self.assertRaisesRegex(NoResourceFound, "More than one"):
            match_arn("foo", arns)

    def test_no_matches(self):
        arns = ["12334/foo", "3313/foo", "1323/foe"]

        with self.assertRaisesRegex(NoResourceFound, "No resource matching"):
            match_arn("hhhhawhs", arns)
