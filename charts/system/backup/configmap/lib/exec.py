import subprocess
from lib import env

def setup_ssh(ctx, nodes):
    run(ctx, f"eval $(ssh-agent -s) && ssh-add {env.ssh_identity}")
    for node in nodes: # required for rsync
        dry(ctx, f'scp {env.ssh_identity} {node}:/tmp/id_ed25519')
        dry(ctx, f'ssh {node} sudo cp /tmp/id_ed25519 /root/.ssh/id_ed25519')

def run(ctx, cmd, check=True, silent=False):
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=False)
    if not silent and res.returncode != 0:
        ctx.error(f"ran: {cmd}: {res.returncode}")
        if res.stdout:
          ctx.error(f"stdout: {res.stdout.strip()}")
        if res.stderr:
          ctx.error(f"stderr: {res.stderr.strip()}")
    if check and res.returncode != 0:
        raise Exception(f"cmd error {res.returncode}: '{cmd}'\n...stderr...\n{res.stdout.strip()}\n...stderr...\n{res.stderr.strip()}")
    return res

def dry(ctx, cmd):
    if env.no_dry_run: run(ctx, cmd)
    else: ctx.warn(f"dry-run: {cmd}")

def out(ctx, cmd, check=True, silent=False):
    return run(ctx, cmd, check=check, silent=silent).stdout.strip()
