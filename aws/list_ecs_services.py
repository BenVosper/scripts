"""
A command-line utility for listing ECS services for all available clusters.

By default prints cluster and services names like so:

    cluster_a service_a
    cluster_a service_b
    cluster_b service_c

Pass '--arn' argument to print full arns instead:

    arn:aws:ecs:~~~~/cluster_a arn:aws:ecs:~~~~/service_a
    arn:aws:ecs:~~~~/cluster_a arn:aws:ecs:~~~~/service_b
    arn:aws:ecs:~~~~/cluster_b arn:aws:ecs:~~~~/service_c
"""

import argparse
import sys

from common import (
    ListClusters,
    ListServices,
)


def get_name_from_arn(arn):
    *_, name = arn.split("/")
    return name


def main(show_arns=False):
    clusters = ListClusters.get_all()

    for cluster_arn in clusters:
        services = ListServices.get_all(cluster_arn=cluster_arn)
        cluster_name = get_name_from_arn(cluster_arn)
        for service_arn in services:
            service_name = get_name_from_arn(service_arn)

            if show_arns:
                print(cluster_arn, service_arn)
            else:
                print(cluster_name, service_name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="List ECS services for all available clusters"
    )
    parser.add_argument(
        "--arn", action="store_true", help="Print full ARNs instead of just names"
    )

    args = parser.parse_args()

    main(show_arns=args.arn)
