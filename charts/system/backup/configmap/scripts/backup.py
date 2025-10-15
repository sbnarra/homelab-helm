#!/usr/bin/env python3

from concurrent.futures import ThreadPoolExecutor
import exec
import k8
import context
import env
import data

def main():
    print(f"NO_DRY_RUN={env.no_dry_run},CONCURRENCY_NAMESPACE={env.namespace_concurrency},CONCURRENCY_DEPLOYMENT={env.deployment_concurrency}")
    with ThreadPoolExecutor(max_workers=env.namespace_concurrency, thread_name_prefix="ns") as namespaceExecutor:
        with ThreadPoolExecutor(max_workers=env.deployment_concurrency, thread_name_prefix="thread") as deploymentExecutor:
            backup_cluster(namespaceExecutor, deploymentExecutor)

def backup_cluster(namespaceExecutor, deploymentExecutor):
    all_nodes = set()
    namespace_nodes = dict()
    backup_nodes = set() # nodes flagged to store backups

    for namespace in k8.resource_names("namespace"):
        if not env.include_namespace(namespace):
            print(f"excluding {namespace}")
            continue
        node_ip = k8.pv_node_ip(namespace)
        if not node_ip: 
            print(f"no persitence node found for namespace '{namespace}'")
            continue
        all_nodes.add(node_ip)
        namespace_nodes[namespace] = node_ip
        if k8.get_nodes_by_label({"node/backups": 1, "node/host": node_ip}):
            backup_nodes.add(node_ip)

    exec.setup_ssh(all_nodes)

    futures = []
    for namespace, node in namespace_nodes.items():
        f = namespaceExecutor.submit(backup_namespace, node, namespace, backup_nodes, deploymentExecutor)
        futures.append(f)
    if exec.wait_for_tasks(futures, "backup_cluster"):
        raise Exception("backup has failures")

def backup_namespace(node, namespace, backup_nodes, executor):
    futures = []
    for deployment in k8.resource_names("deployment", namespace):
        ctx = context.Context(node, namespace, deployment)
        if data.exists(ctx):
            futures.append(executor.submit(backup_deployment, ctx, backup_nodes))
    if exec.wait_for_tasks(futures, f"backup_namespace: {node}/{namespace}"):
        raise Exception()

def backup_deployment(ctx, backup_nodes):
    potential_backup_nodes = [backup_node for backup_node in backup_nodes if backup_node != ctx.node]
    backup_node = potential_backup_nodes[0] if potential_backup_nodes else None
    if not backup_node:
        ctx.throw(f"unable to backup, no primary backup node: node={ctx.node},potential_backup_nodes={potential_backup_nodes}")
    backup_distribution_nodes = [node for node in potential_backup_nodes if node != backup_node]

    replicas = k8.scale_down(ctx)
    try: data.sync(ctx, ctx.node, backup_node)
    except Exception: 
        k8.scale_up(ctx, replicas)
        raise

    k8_scale_up = threading.Thread(target=k8.scale_up, args=(ctx, replicas))
    k8_scale_up.start()

    for backup_distribution_node in backup_distribution_nodes:
        if backup_node != backup_distribution_node:
            try: data.sync(ctx, backup_node, backup_distribution_node)
            except Exception as e:
                ctx.error(f"backup distribution failed {backup_node} -> {backup_distribution_node}: {e}", e)
                pass

    if k8_scale_up:
        k8_scale_up.join()

if __name__ == "__main__":
    main()