from lib import exec
import time

def exists(ctx):
    return exec.run(ctx, f"ssh {ctx.node} ls /lab/persistence/{ctx.namespace}/{ctx.deployment}", check=False, silent=True).returncode == 0

def sync(ctx, src_node, src_dir, target_node, target_dir):
    rsync = 'rsync -avz --delete --rsync-path=\\"sudo rsync\\"'
    rsync_ssh = '-e \\"ssh -F /home/lab/.ssh/config\\"'

    ctx.debug(f"backing up {src_node} -> {target_node}")

    start_time = time.time()
    exec.dry(ctx, f'ssh -A {src_node} "sudo {rsync} {rsync_ssh} {src_dir} lab@{target_node}:{target_dir}"')
    duration = time.time() - start_time

    minutes = int(duration // 60)
    seconds = int(duration % 60)
    ctx.info(f"backed up {src_node} -> {target_node} in {minutes:02d}:{seconds:02d}")
