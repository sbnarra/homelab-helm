
import os

scale_up_timeout = int(os.getenv("SCALE_UP_TIMEOUT", 20))
scale_down_timeout = int(os.getenv("SCALE_DOWN_TIMEOUT", 30))
namespace_concurrency = int(os.getenv("CONCURRENCY_NAMESPACE", 1))
deployment_concurrency = int(os.getenv("CONCURRENCY_DEPLOYMENT", 1))
no_dry_run = os.getenv("NO_DRY_RUN", 0) == "1"
exclude_namespaces = os.getenv("EXCLUDE_NAMESPACES", "")
exclude_namespaces = [ns.strip() for ns in exclude_namespaces.split(",") if ns.strip()]
include_namespaces = os.getenv("INCLUDE_NAMESPACES", "")
include_namespaces = [ns.strip() for ns in include_namespaces.split(",") if ns.strip()]