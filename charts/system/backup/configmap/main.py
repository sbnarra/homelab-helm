import sys
sys.dont_write_bytecode = True

from lib import env, job, context, exec
from concurrent.futures import ThreadPoolExecutor
from backup import nodes, persistence, directory

def init():
    ctx = context.Context("init")
    all_nodes, namespace_nodes = nodes.namespace(ctx)
    backup_nodes = nodes.find(ctx, all_nodes, "backups")
    exec.setup_ssh(ctx, all_nodes)

    job.queue(ctx, persistence.backup, namespace_nodes, backup_nodes)
    job.queue(ctx, directory.backup, all_nodes, backup_nodes, "workspace")
    job.queue(ctx, directory.backup, all_nodes, backup_nodes, "terraform-backend")

if __name__ == "__main__":
    ctx = context.Context("main")
    for k in env.resolved: ctx.info(f"{k}={env.resolved[k]}")
    with ThreadPoolExecutor(max_workers=env.job_concurrency, thread_name_prefix="j") as job_executor:
        job.init(job_executor)
        job.queue(ctx, init)
        job.wait(ctx)
