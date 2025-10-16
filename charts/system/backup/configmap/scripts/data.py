import exec
import time

def exists(ctx):
    return exec.run(f"ssh {ctx.node} ls /lab/persistence/{ctx.namespace}/{ctx.deployment}", check=False, silent=True).returncode == 0

def sync(ctx, src_node, target_node):
    src = f"/lab/persistence/{ctx.namespace}/{ctx.deployment}/"
    dst = f"{target_node}:/lab/persistence/{ctx.namespace}/{ctx.deployment}"
    rsync = 'rsync -avz --delete --rsync-path=\\"sudo rsync\\"'
    rsync_ssh = '-e \\"ssh -F /home/lab/.ssh/config\\"'

    ctx.debug(f"backing up {src_node} -> {target_node}")

    start_time = time.time()
    exec.dry(f'ssh -A {src_node} "sudo {rsync} {rsync_ssh} {src} lab@{dst}"')
    duration = time.time() - start_time

    minutes = int(duration // 60)
    seconds = int(duration % 60)
    ctx.info(f"backed up {src_node} -> {target_node} in {minutes:02d}:{seconds:02d}")
