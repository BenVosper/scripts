"""
A command-line utility for getting the private DNS of an ECS instance for a given cluster and
service.

Useful for obtaining SSH access to a particular service where you don't care exactly which instance
you're accessing.

Usage:

    Provide:

        <cluster> - The name of the cluster you'd like to access

        <servive> - The name of the service you'd like to access

    If a service can be identified from your input parameters, the private DNS of the first ECS
    instance of the first running task associated with this service will be printed to stdout.

    Errors will be raised if no service can be identified or there are no running tasks.
"""

import argparse
import sys

from common import BaseCommand, BasePaginatedCommand, NonZeroErrorCode


class NoResourceFound(Exception):
    pass


class ListClusters(BasePaginatedCommand):

    base_command = "aws ecs list-clusters"

    results_key = "clusterArns"


class ListServices(BasePaginatedCommand):

    base_command = "aws ecs list-services"

    results_key = "serviceArns"

    def __init__(self, cluster_arn, **kwargs):
        self.cluster_arn = cluster_arn
        super().__init__(**kwargs)

    @property
    def call_args(self):
        args = super().call_args
        args += ["--cluster", self.cluster_arn]
        return args


class ListTasks(BaseCommand):

    base_command = "aws ecs list-tasks"
    desired_status = "RUNNING"

    results_key = "taskArns"

    def __init__(self, cluster_arn, service_arn):
        self.cluster_arn = cluster_arn
        self.service_arn = service_arn

    @property
    def call_args(self):
        args = super().call_args
        args += ["--cluster", self.cluster_arn]
        args += ["--service", self.service_arn]
        args += ["--desired-status", self.desired_status]
        return args


class DescribeTasks(BaseCommand):

    base_command = "aws ecs describe-tasks"

    results_key = "tasks"
    container_instance_key = "containerInstanceArn"

    def __init__(self, cluster_arn, task_arn):
        self.cluster_arn = cluster_arn
        self.task_arn = task_arn

    @property
    def call_args(self):
        args = super().call_args
        args += ["--cluster", self.cluster_arn]
        args += ["--tasks", self.task_arn]
        return args


class DescribeContainerInstances(BaseCommand):

    base_command = "aws ecs describe-container-instances"

    results_key = "containerInstances"
    ec2_instance_key = "ec2InstanceId"

    def __init__(self, cluster_arn, container_arn):
        self.cluster_arn = cluster_arn
        self.container_arn = container_arn

    @property
    def call_args(self):
        args = super().call_args
        args += ["--cluster", self.cluster_arn]
        args += ["--container-instances", self.container_arn]
        return args


class DescribeEc2Instances(BaseCommand):

    base_command = "aws ec2 describe-instances"

    reservations_key = "Reservations"
    instances_key = "Instances"
    dns_url_key = "PrivateDnsName"

    def __init__(self, instance_id):
        self.instance_id = instance_id

    @property
    def call_args(self):
        args = super().call_args
        args += ["--instance-ids", self.instance_id]
        return args


def match_arn(name, arns):
    matches = [arn for arn in arns if name in arn]
    if not matches:
        available = "\n".join(arns)
        msg = f"No resource matching name {name} found. Available resources:\n{available}"
        raise NoResourceFound(msg)
    elif len(matches) > 1:
        available = "\n".join(matches)
        msg = f"More than one resource found for name {name}:\n{available}"
        raise NoResourceFound(msg)
    return matches[0]


def main(cluster_name, service_name):
    clusters = ListClusters.get_all()
    cluster_arn = match_arn(cluster_name, clusters)

    services = ListServices.get_all(cluster_arn=cluster_arn)
    service_arn = match_arn(service_name, services)

    tasks_command = ListTasks(cluster_arn=cluster_arn, service_arn=service_arn)
    task_arns = tasks_command()[ListTasks.results_key]

    if not task_arns:
        msg = f"No running tasks found for service {service_arn}"
        raise NoResourceFound(msg)

    task_arn = task_arns[0]
    task_command = DescribeTasks(cluster_arn=cluster_arn, task_arn=task_arn)
    task = task_command()[DescribeTasks.results_key][0]

    container_arn = task[DescribeTasks.container_instance_key]
    container_command = DescribeContainerInstances(
        cluster_arn=cluster_arn, container_arn=container_arn
    )
    container = container_command()[DescribeContainerInstances.results_key][0]
    ec2_instance_id = container[DescribeContainerInstances.ec2_instance_key]

    ec2_instance_command = DescribeEc2Instances(instance_id=ec2_instance_id)
    reservation = ec2_instance_command()[DescribeEc2Instances.reservations_key][0]
    instance = reservation[DescribeEc2Instances.instances_key][0]
    return instance[DescribeEc2Instances.dns_url_key]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Get ECS private DNS URL for given service")
    parser.add_argument("cluster", type=str)
    parser.add_argument("service", type=str)

    args = parser.parse_args()

    try:
        print(main(args.cluster, args.service))
    except (NonZeroErrorCode, NoResourceFound) as error:
        print(str(error))
        sys.exit(1)
