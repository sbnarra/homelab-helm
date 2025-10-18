from lib import log
import os

resolved = dict()

def get(key, default, parse = lambda v: v):
    resolved[key] = parse(os.getenv(key, default))
    return resolved[key]

def as_array(k):
    return get(k, "", lambda v: [ns.strip() for ns in v.split(",") if ns.strip()])
  
def as_bool(k):
  return get(k, "0", lambda v: v == "1")

def include_namespace(namespace):
    return namespace not in exclude_namespaces or namespace in include_namespaces

no_dry_run = as_bool("NO_DRY_RUN")
log_level = get("LOG_LEVEL", "DEBUG", lambda v: log.Level[v])
job_concurrency = get("JOB_CONCURRENCY", "1", int)
scale_up_timeout = get("SCALE_UP_TIMEOUT", "20", int)
scale_down_timeout = get("SCALE_DOWN_TIMEOUT", "30", int)
ssh_identity = get("SSH_IDENTITY", f"{os.getenv("HOME")}/.ssh/id_ed25519")
exclude_namespaces = as_array("EXCLUDE_NAMESPACES")
include_namespaces = as_array("INCLUDE_NAMESPACES")