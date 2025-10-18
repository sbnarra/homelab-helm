from lib import exec, env
import time

def scale_up(ctx, replicas):
    if replicas == 0: return
    _set_deployment_replicas(ctx, 0, replicas)
    if env.no_dry_run:
        try: _wait_deployment_replicas(ctx, replicas, env.scale_up_timeout)
        except Exception as e:
            ctx.error(f"scale up failed: {e}", e)
            pass

def scale_down(ctx):
    replicas = _get_deployment_replicas(ctx)
    if replicas == 0: return 0

    _set_deployment_replicas(ctx, replicas, 0)
    if not env.no_dry_run: return replicas

    try: _wait_deployment_replicas(ctx, 0, env.scale_down_timeout)
    except Exception: 
        _set_deployment_replicas(ctx, 0, replicas)
        raise
    return replicas

def pv_node_ip(ctx, namespace):
    cmd = f"kubectl get pv persistence-{namespace} {_jsonpath(".spec.nfs.server")}"
    return exec.out(ctx, cmd, check=False, silent=True)

def get_nodes_by_label(ctx, labels):
    label_selector = ",".join([f"{k}={v}" for k, v in labels.items()])
    output = exec.out(ctx, f"kubectl get nodes -l {label_selector} {_jsonpath(".items[*].metadata.name")}")
    return output.split()

def _jsonpath(path):
    return "-o jsonpath='{"+path+"}'"

def resource_names(ctx, resource, namespace = "global"):
    output = exec.out(ctx, f"kubectl get {resource} -n {namespace} {_jsonpath(".items[*].metadata.name")}")
    return [name for name in output.split() if name]

def _get_deployment_replicas(ctx):
    result = exec.out(ctx, f"kubectl get deployment -l app.kubernetes.io/name={ctx.deployment} -n {ctx.namespace} -o custom-columns=REPLICAS:.status.replicas --no-headers").strip()
    return int(result) if result and result.isdigit() else 0

def _set_deployment_replicas(ctx, current_replicas, target_replicas):
    ctx.info(f"setting replicas {current_replicas} -> {target_replicas}")
    exec.dry(ctx, f"kubectl scale deployment {ctx.deployment} -n {ctx.namespace} --replicas={target_replicas}")

def _get_deployment_pods_ready(ctx):
    result = exec.out(ctx, f"kubectl get deployment {ctx.deployment} -n {ctx.namespace} {_jsonpath(".status.readyReplicas")}").strip()
    return int(result) if result and result.isdigit() else 0

def _wait_deployment_replicas(ctx, replicas, timeout, log_interval=10):
    duration = 0
    msg = ""
    while True:
        pods_ready = _get_deployment_pods_ready(ctx)
        msg = _wait_deployment_replicas_msg(pods_ready, replicas)

        if pods_ready == replicas:
            break
        duration += 1
        if duration >= timeout:
            ctx.throw(f"{msg} scale timed out after {timeout}s")
        if duration % log_interval == 0:
            ctx.info(f"{msg} after {duration}s, still waiting")
        time.sleep(1)
    ctx.info(_wait_deployment_replicas_msg(pods_ready, replicas))

def _wait_deployment_replicas_msg(pods_ready, replicas):
    return f"has {pods_ready}/{replicas} pods ready"