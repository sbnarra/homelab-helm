#!/usr/bin/env python3

from concurrent.futures import ThreadPoolExecutor
import exec
import k8
import context
import env
import data

R5C, RX4, OP5, RP4 = "192.168.1.1", "192.168.1.2", "192.168.1.3", "192.168.1.4"

def main():
    
    print(f"NO_DRY_RUN={env.no_dry_run},CONCURRENCY_NAMESPACE={env.namespace_concurrency},CONCURRENCY_DEPLOYMENT={env.deployment_concurrency}")

    with ThreadPoolExecutor(max_workers=env.namespace_concurrency) as namespaceExecutor:
        with ThreadPoolExecutor(max_workers=env.deployment_concurrency, thread_name_prefix="backup") as deploymentExecutor:
            backup_cluster(namespaceExecutor, deploymentExecutor)

def backup_cluster(namespaceExecutor, deploymentExecutor):
    nodes = set()
    namespace_nodes = dict()
    for namespace in k8.resource_names("namespace"):
        if (namespace in env.exclude_namespaces
            or (env.include_namespaces and namespace not in env.include_namespaces)):
            print(f"excluding {namespace}")
            continue

        node = k8.pv_node(namespace)
        if node: 
            nodes.add(node)
            namespace_nodes[namespace] = node
        else:
            print(f"no persitence node found for namespace '{namespace}'")

    exec.setup_ssh(nodes)

    futures = []
    for namespace, node in namespace_nodes.items():
        f = namespaceExecutor.submit(backup_namespace, node, namespace, deploymentExecutor)
        futures.append(f)
    if exec.wait_for_tasks(futures, "backup_cluster"):
        raise Exception("backup has failures")

def backup_namespace(node, namespace, executor):
    futures = []
    for deployment in k8.resource_names("deployment", namespace):
        ctx = context.Context(node, namespace, deployment)
        if data.exists(ctx):
            futures.append(executor.submit(backup_deployment, ctx))
    if exec.wait_for_tasks(futures, f"backup_namespace: {node}/{namespace}"):
        raise Exception()

def backup_deployment(ctx):
    replicas = k8.scale_down(ctx)

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

    try: data.sync(ctx, ctx.node, primary_node)
    finally: k8.scale_up(ctx, replicas)

    secondary_nodes = [] # [RX4, RP4]
    # secondary_nodes = get_nodes_by_label("backup/role", "secondary")
    for secondary_node in secondary_nodes:
        if primary_node != secondary_node:
            data.sync(ctx, primary_node, secondary_node)

if __name__ == "__main__":
    main()