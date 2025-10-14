import exec

def exists(ctx):
    return exec.run(f"ssh {ctx.node} ls /lab/persistence/{ctx.namespace}/{ctx.deployment}", check=False, silent=True).returncode == 0

def sync(ctx, src_node, target_node):
    src = f"/lab/persistence/{ctx.namespace}/{ctx.deployment}/"
    dst = f"{target_node}:/lab/persistence/{ctx.namespace}/{ctx.deployment}"
    rsync = 'rsync -avz --delete --rsync-path=\\"sudo rsync\\"'
    rsync_ssh = '-e \\"ssh -F /home/lab/.ssh/config\\"'

    ctx.info(f"backing up to {target_node}")
    exec.dry(f'ssh -A {src_node} "sudo {rsync} {rsync_ssh} {src} lab@{dst}"')
