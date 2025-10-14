#!/usr/bin/env python3

import subprocess
import argparse
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import time
import traceback

def main():
    namespace_concurrency = int(os.getenv("CONCURRENCY_NAMESPACE", 1))
    deployment_concurrency = int(os.getenv("CONCURRENCY_DEPLOYMENT", 1))
    no_dry_run = os.getenv("NO_DRY_RUN", 0) == "1"
    if no_dry_run:
        raise Exception("unsafe")
    
    print(f"NO_DRY_RUN={no_dry_run},CONCURRENCY_NAMESPACE={namespace_concurrency},CONCURRENCY_DEPLOYMENT={deployment_concurrency}")

    setup_ssh(no_dry_run)
    with ThreadPoolExecutor(max_workers=namespace_concurrency) as namespaceExecutor:
        with ThreadPoolExecutor(max_workers=deployment_concurrency) as deploymentExecutor:
            backup_cluster(no_dry_run, namespaceExecutor, deploymentExecutor)

def backup_cluster(no_dry_run, namespaceExecutor, deploymentExecutor):
    nodes = set()
    namespace_nodes = dict()
    for namespace in k8_resource_names("namespace"):
        node = k8_pv_node(namespace)
        if node: 
            nodes.add(node)
            namespace_nodes[namespace] = node
        else:
            print(f"no persitence node found for namespace '{namespace}'")

    for node in nodes:
        dry_run(f'scp /root/.ssh/id_ed25519 {node}:/tmp/id_ed25519', no_dry_run)
        dry_run(f'ssh {node} sudo cp /tmp/id_ed25519 /root/.ssh/id_ed25519', no_dry_run)

    futures = []
    for namespace, node in namespace_nodes.items():
        f = namespaceExecutor.submit(backup_namespace, node, namespace, no_dry_run, deploymentExecutor)
        futures.append(f)
    if wait_for_tasks(futures, "backup_cluster"):
        raise Exception("backup has failures")

def backup_namespace(node, namespace, no_dry_run, executor):
    futures = []
    for deployment in k8_resource_names("deployment", namespace):
        if data_exists(node, namespace, deployment):
            futures.append(executor.submit(backup_deployment, node, namespace, deployment, no_dry_run))
    
    if wait_for_tasks(futures, f"backup_namespace: {node}/{namespace}"):
        raise Exception()


def backup_deployment(node, namespace, deployment, no_dry_run):
    # TODO: derive this via labels?
    R5C, RX4, OP5, RP4 = "192.168.1.1", "192.168.1.2", "192.168.1.3", "192.168.1.4"
    BACKUP_NODE_1, BACKUP_NODE_2, BACKUP_NODE_EXTRAS = R5C, OP5, []
    BACKUP_NODES = [BACKUP_NODE_1, BACKUP_NODE_2, *BACKUP_NODE_EXTRAS]

    replicas = k8_deployment_get_replica(namespace, deployment)
    print(f"{node}/{namespace}/{deployment}: has {replicas} replicas")
    if replicas > 0:
        k8_deployment_set_replica(node, namespace, deployment, 0, no_dry_run)
        if no_dry_run:
            try: k8_deployment_replica_wait(namespace, deployment)
            except Exception: 
                k8_deployment_set_replica(node, namespace, deployment, replicas, no_dry_run)
                raise

    backup_node = BACKUP_NODE_1 if node == BACKUP_NODE_2 else BACKUP_NODE_2
    try: data_sync(node, namespace, deployment, backup_node, no_dry_run)
    finally: replicas > 0 and k8_deployment_set_replica(node, namespace, deployment, replicas, no_dry_run)

    for backup_node_extra in BACKUP_NODE_EXTRAS:
        if backup_node != backup_node_extra:
            data_sync(backup_node, namespace, deployment, backup_node_extra, no_dry_run)

def setup_ssh(no_dry_run):
    run(f"eval $(ssh-agent -s) && ssh-add /root/.ssh/id_ed25519")

def data_exists(node, namespace, deployment):
    return run(f"ssh {node} ls /lab/persistence/{namespace}/{deployment}", check=False).returncode == 0

def data_sync(node, namespace, deployment, backup_node, no_dry_run):
    src = f"/lab/persistence/{namespace}/{deployment}/"
    dst = f"{backup_node}:/lab/persistence/{namespace}/{deployment}"
    rsync = 'rsync -avz --delete --rsync-path=\\"sudo rsync\\"'
    rsync_ssh = '-e \\"ssh -F /home/lab/.ssh/config\\"'

    print(f"{node}/{namespace}/{deployment}: backing up to {backup_node}")
    dry_run(f'ssh -A {node} "sudo {rsync} {rsync_ssh} {src} lab@{dst}"', no_dry_run)

def k8_pv_node(namespace):
    cmd = f"kubectl get pv persistence-{namespace}" + " -o jsonpath='{.spec.nfs.server}'"
    return out(cmd, check=False, silent=True)

def k8_resource_names(resource, namespace = "global"):
    output = out(f"kubectl get {resource} -n {namespace}" + " -o jsonpath='{.items[*].metadata.name}'")
    return [name for name in output.split() if name]

def k8_deployment_get_replica(namespace, deployment):
    result = out(f"kubectl get deployment -l app.kubernetes.io/name={deployment} -n {namespace} -o custom-columns=REPLICAS:.status.replicas --no-headers").strip()
    return int(result) if result and result.isdigit() else 0

def k8_deployment_set_replica(node, namespace, deployment, replicas, no_dry_run):
    print(f"{node}/{namespace}/{deployment}: setting replicas to {replicas}")
    dry_run(f"kubectl scale deployment {deployment} -n {namespace} --replicas={replicas}", no_dry_run)

def k8_deployment_replica_wait(namespace, deployment, timeout=300, log_interval=10):
    duration = 0
    while True:
        pod_count = int(run(f"kubectl get pods -l app.kubernetes.io/name={deployment} -n {namespace} --no-headers 2>/dev/null | wc -l").stdout.strip() or 0)
        if pod_count == 0:
            break
        duration += 1
        if duration >= timeout:
            raise Exception(f"({pod_count} pods) scale down timed out after {timeout}s: {namespace}/{deployment}")
        if duration % log_interval == 0:
            print(f"({pod_count} pods) scale down waiting for {duration}s: {namespace}/{deployment}")
        time.sleep(1)

def dry_run(cmd, no_dry_run=True):
    if no_dry_run:
        return run(cmd)
    print(f"dry-run: {cmd}")

def out(cmd, check=True, silent=False):
    return run(cmd, check=check, silent=silent).stdout.strip()

def run(cmd, check=True, silent=False):
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=False)
    if not silent and res.returncode != 0:
        print(f"ran: {cmd}: {res.returncode}")
        print(f"stderr: {res.stdout}")
        print(f"stderr: {res.stderr}")
    if check and res.returncode != 0:
        raise Exception(f"cmd error {res.returncode}: '{cmd}'\n...stderr...\n{res.stdout}\n...stderr...\n{res.stderr}")
    return res

def wait_for_tasks(futures, error_msg):
    errors = []
    for f in futures:
        try: f.result()
        except Exception as e:
            print(f"[ERROR] {error_msg}: {e}")
            traceback.print_exc() # full stack
            errors.append(e)
    return errors

if __name__ == "__main__":
    main()