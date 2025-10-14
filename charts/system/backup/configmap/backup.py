#!/usr/bin/env python3

import os
from concurrent.futures import ThreadPoolExecutor

import run
import k8
import context

R5C, RX4, OP5, RP4 = "192.168.1.1", "192.168.1.2", "192.168.1.3", "192.168.1.4"

def main():
    namespace_concurrency = int(os.getenv("CONCURRENCY_NAMESPACE", 1))
    deployment_concurrency = int(os.getenv("CONCURRENCY_DEPLOYMENT", 1))
    no_dry_run = os.getenv("NO_DRY_RUN", 0) == "1"
    
    print(f"NO_DRY_RUN={no_dry_run},CONCURRENCY_NAMESPACE={namespace_concurrency},CONCURRENCY_DEPLOYMENT={deployment_concurrency}")

    with ThreadPoolExecutor(max_workers=namespace_concurrency) as namespaceExecutor:
        with ThreadPoolExecutor(max_workers=deployment_concurrency, thread_name_prefix="backup") as deploymentExecutor:
            backup_cluster(no_dry_run, namespaceExecutor, deploymentExecutor)

def backup_cluster(no_dry_run, namespaceExecutor, deploymentExecutor):
    exclude_namespaces = os.getenv("EXCLUDE_NAMESPACES", "")
    exclude_namespaces = [ns.strip() for ns in exclude_namespaces.split(",") if ns.strip()]
    include_namespaces = os.getenv("INCLUDE_NAMESPACES", "")
    include_namespaces = [ns.strip() for ns in include_namespaces.split(",") if ns.strip()]

    nodes = set()
    namespace_nodes = dict()
    for namespace in k8.resource_names("namespace"):
        if (namespace in exclude_namespaces
            or (include_namespaces and namespace not in include_namespaces)):
            print(f"excluding {namespace}")
            continue

        node = k8.pv_node(namespace)
        if node: 
            nodes.add(node)
            namespace_nodes[namespace] = node
        else:
            print(f"no persitence node found for namespace '{namespace}'")

    run.setup_ssh(no_dry_run, nodes)

    futures = []
    for namespace, node in namespace_nodes.items():
        f = namespaceExecutor.submit(backup_namespace, node, namespace, no_dry_run, deploymentExecutor)
        futures.append(f)
    if run.wait_for_tasks(futures, "backup_cluster"):
        raise Exception("backup has failures")

def backup_namespace(node, namespace, no_dry_run, executor):
    futures = []
    for deployment in k8.resource_names("deployment", namespace):
        ctx = context.Context(node, namespace, deployment, no_dry_run)
        if run.data_exists(ctx):
            futures.append(executor.submit(backup_deployment, ctx))
    if run.wait_for_tasks(futures, f"backup_namespace: {node}/{namespace}"):
        raise Exception()

def backup_deployment(ctx):
    scale_up_timeout = int(os.getenv("SCALE_UP_TIMEOUT", 20))
    scale_down_timeout = int(os.getenv("SCALE_DOWN_TIMEOUT", 30))

    replicas = k8.scale_down(ctx, timeout=scale_up_timeout)

    primary_nodes = [R5C, OP5]
    # TODO: must be 2 nodes... when primary = node, use other to allow offline backup
    # if only 1: when node same as primary,
    #   unable to run secondary without corrupt data risk as using live data
    # if more than 2: will always end up with one node missing

    # TODO: move get_nodes_by_label higher to only call once at start, 
    # maybe object for all this being passed around
    # primary_nodes = get_nodes_by_label("backup/role", "primary")
    primary_node = next((primary_node for primary_node in primary_nodes if primary_node != ctx.node), None)
    if not primary_node:
        ctx.throw("unable to backup, no primary backup node")

    try: run.data_sync(ctx, ctx.node, primary_node)
    finally: k8.scale_up(ctx, replicas, timeout=scale_down_timeout)

    secondary_nodes = [] # [RX4, RP4]
    # secondary_nodes = get_nodes_by_label("backup/role", "secondary")
    for secondary_node in secondary_nodes:
        if primary_node != secondary_node:
            run.data_sync(ctx, primary_node, secondary_node)

if __name__ == "__main__":
    main()