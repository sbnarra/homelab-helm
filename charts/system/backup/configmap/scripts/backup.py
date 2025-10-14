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

    with ThreadPoolExecutor(max_workers=env.namespace_concurrency, thread_name_prefix="ns") as namespaceExecutor:
        with ThreadPoolExecutor(max_workers=env.deployment_concurrency, thread_name_prefix="thread") as deploymentExecutor:
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

    primary_nodes = [R5C, OP5]
    # primary_nodes = k8.get_nodes_by_label("backup/role", "primary")

    potential_primary_nodes = [primary_node for primary_node in primary_nodes if primary_node != ctx.node]
    primary_node = potential_primary_nodes[0] if potential_primary_nodes else None
    if not primary_node:
        ctx.throw(f"unable to backup, no primary backup node: node={ctx.node}potential_primary_nodes={potential_primary_nodes}")

    secondary_nodes = [] # [RX4, RP4]
    # secondary_nodes = k8.get_nodes_by_label("backup/role", "secondary")

    non_primary_nodes = [node for node in potential_primary_nodes if node != primary_node]
    secondary_nodes.extend(non_primary_nodes)

    replicas = k8.scale_down(ctx)
    try: data.sync(ctx, ctx.node, primary_node)
    finally: k8.scale_up(ctx, replicas)
 
    for secondary_node in secondary_nodes:
        if primary_node != secondary_node:
            try: data.sync(ctx, primary_node, secondary_node)
            except Exception as e:
                ctx.error(f"secondary backup failed {primary_node} -> {secondary_node}: {e}", e)
                pass

if __name__ == "__main__":
    main()