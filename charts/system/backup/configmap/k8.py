import run
import time

def scale_up(ctx, replicas, timeout):
    if replicas == 0: return
    _set_deployment_replicas(ctx, replicas)
    if ctx.no_dry_run:
        try: _wait_deployment_replicas(ctx, replicas, timeout)
        except Exception as e:
            ctx.error(f"scale up failed: {e}", e)
            pass

def scale_down(ctx, timeout):
    replicas = _get_deployment_replicas(ctx)
    ctx.info(f"has {replicas} replicas")
    if replicas == 0: return 0

    _set_deployment_replicas(ctx, 0)
    if not ctx.no_dry_run: return replicas

    try: _wait_deployment_replicas(ctx, 0, timeout)
    except Exception: 
        _set_deployment_replicas(ctx, replicas)
        raise
    return replicas

def pv_node(namespace):
    cmd = f"kubectl get pv persistence-{namespace} {_jsonpath(".spec.nfs.server")}"
    return run.out(cmd, check=False, silent=True)

def get_nodes_by_label(key, value):
    output = run.out(f"kubectl get nodes -l {key}={value} {_jsonpath(".items[*].metadata.name")}")
    return output.split()

def _jsonpath(path):
    return "-o jsonpath='{"+path+"}'"

def resource_names(resource, namespace = "global"):
    output = run.out(f"kubectl get {resource} -n {namespace} {_jsonpath(".items[*].metadata.name")}")
    return [name for name in output.split() if name]

def _get_deployment_replicas(ctx):
    result = run.out(f"kubectl get deployment -l app.kubernetes.io/name={ctx.deployment} -n {ctx.namespace} -o custom-columns=REPLICAS:.status.replicas --no-headers").strip()
    return int(result) if result and result.isdigit() else 0

def _set_deployment_replicas(ctx, replicas):
    ctx.info(f"setting replicas to {replicas}")
    run.dry(f"kubectl scale deployment {ctx.deployment} -n {ctx.namespace} --replicas={replicas}", ctx.no_dry_run)

def _get_deployment_pods_ready(ctx):
    result = run.out(f"kubectl get deployment {ctx.deployment} -n {ctx.namespace} {_jsonpath(".status.readyReplicas")}").strip()
    return int(result) if result and result.isdigit() else 0

def _wait_deployment_replicas(ctx, replicas, timeout, log_interval=10):
    duration = 0
    msg = ""
    while True:
        pods_ready = _get_deployment_pods_ready(ctx)
        msg = _wait_deployment_replicas_msg(ctx, pods_ready, replicas)

        if pods_ready == replicas:
            break
        duration += 1
        if duration >= timeout:
            ctx.throw(f"{msg} scale timed out after {timeout}s")
        if duration % log_interval == 0:
            ctx.info(f"{msg} after {duration}s, still waiting")
        time.sleep(1)
    ctx.info(_wait_deployment_replicas_msg(ctx, pods_ready, replicas))

def _wait_deployment_replicas_msg(ctx, pods_ready, replicas):
    return f"has {pods_ready}/{replicas} ready"