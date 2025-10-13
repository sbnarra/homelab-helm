#!/usr/bin/env python3

import subprocess
import argparse
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import time

R5C, RX4, OP5, RP4 = "192.168.1.1", "192.168.1.2", "192.168.1.3", "192.168.1.4"
BACKUP_NODE_1, BACKUP_NODE_2, BACKUP_NODE_EXTRAS = R5C, OP5, [RX4, RP4]
NAMESPACE_BACKUPS = [
    (R5C, "network"),
    (RX4, "media"),
    (RX4, "starr"),
    (OP5, "tools"),
    (OP5, "ai"),
    (OP5, "printer"),
    (RP4, "system")
]
ssh = "ssh -A -o StrictHostKeyChecking=no -i /id_ed25519 lab@"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-dry-run", action="store_true", help="Execute commands")
    parser.add_argument("--max-jobs", type=int, default=1, help="Max concurrent jobs")
    args = parser.parse_args()
    print(f"--no-dry-run={args.no_dry_run} --max-jobs={args.max_jobs}")

    setup_ssh()

    futures = []
    with ThreadPoolExecutor(max_workers=args.max_jobs) as namespaceExecutor:
        with ThreadPoolExecutor(max_workers=args.max_jobs) as deploymentExecutor:
            for node, namespace in NAMESPACE_BACKUPS:
                f = namespaceExecutor.submit(backup_namespace, node, namespace, args.no_dry_run, deploymentExecutor)
                futures.append(f)
            [f.result() for f in futures]

def backup_namespace(node, namespace, no_dry_run, executor):
    futures = []
    for deployment in k8_deployment_names(namespace):
        if data_exists(node, namespace, deployment):
            futures.append(executor.submit(backup_deployment, node, namespace, deployment, no_dry_run))
    [f.result() for f in futures]

def backup_deployment(node, namespace, deployment, no_dry_run):
    replicas = k8_deployment_get_replica(namespace, deployment)
    if replicas > 0:
        k8_deployment_set_replica(namespace, deployment, 0, no_dry_run)
        if no_dry_run:
            k8_deployment_replica_wait(namespace, deployment)

    backup_node = BACKUP_NODE_1 if node == BACKUP_NODE_2 else BACKUP_NODE_2
    data_sync(node, namespace, deployment, backup_node, no_dry_run)

    replicas > 0 and k8_deployment_set_replica(namespace, deployment, replicas, no_dry_run)

    for backup_node_extra in BACKUP_NODE_EXTRAS:
        if backup_node != backup_node_extra:
            data_sync(backup_node, namespace, deployment, backup_node_extra, no_dry_run)

def setup_ssh():
    run("eval $(ssh-agent -s) && ssh-add /id_ed25519")

def data_exists(node, namespace, deployment):
    return run(f"{ssh}{node} ls /lab/persistence/{namespace}/{deployment}", check=False).returncode == 0

def data_sync(node, namespace, deployment, backup_node, no_dry_run):
    src = f"/lab/persistence/{namespace}/{deployment}/"
    dst = f"{backup_node}:/lab/persistence/{namespace}/{deployment}"
    print(f"rsync :: {namespace}/{deployment} {node} -> {backup_node}")
    dry_run(f'{ssh}{node} "sudo rsync -avz --delete --rsync-path=\\"sudo rsync\\" {src} lab@{dst}"', no_dry_run)

def k8_deployment_names(namespace):
    deployments = out(f"kubectl get deployments -n {namespace} -o custom-columns=:metadata.name --no-headers").split('\n')
    return [deployment.strip() for deployment in deployments if deployment.strip()]

def k8_deployment_get_replica(namespace, deployment):
    result = out(f"kubectl get deployment -l app.kubernetes.io/name={deployment} -n {namespace} -o custom-columns=REPLICAS:.status.replicas --no-headers").strip()
    return int(result) if result and result.isdigit() else 0

def k8_deployment_set_replica(namespace, deployment, replicas, no_dry_run):
    dry_run(f"kubectl scale --replicas={replicas} {deployment} -n {namespace}", no_dry_run)

def k8_deployment_replica_wait(namespace, deployment, timeout=60, log_interval=10):
    duration = 0
    while True:
        pod_count = int(run(f"kubectl get pods -l app.kubernetes.io/name={deployment} -n {namespace} --no-headers 2>/dev/null | wc -l").stdout.strip() or 0)
        if pod_count == 0:
            break

        duration += 1
        if duration >= timeout:
            print(f"({pod_count} pods) scale down timed out after {timeout}s: {namespace}/{deployment}")
            break
        if duration % log_interval == 0:
            print(f"({pod_count} pods) scale down waiting for {duration}s: {namespace}/{deployment}")
        time.sleep(1)

def dry_run(cmd, no_dry_run=True):
    if no_dry_run:
        return run(cmd)
    print(f"dry-run: {cmd}")

def out(cmd):
    return run(cmd).stdout.strip()

def run(cmd, check=True):
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=check, executable="/bin/bash")
    # if res.returncode != 0:
    #     print(f"ran: {cmd}: {res.returncode}")
    #     print(f"stderr: {res.stdout}")
    #     print(f"stderr: {res.stderr}")
    return res

if __name__ == "__main__":
    main()