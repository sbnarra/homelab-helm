import subprocess
import traceback

def setup_ssh(no_dry_run, nodes):
    _run(f"eval $(ssh-agent -s) && ssh-add /root/.ssh/id_ed25519")
    for node in nodes: # required for rsync
        dry(f'scp /root/.ssh/id_ed25519 {node}:/tmp/id_ed25519', no_dry_run)
        dry(f'ssh {node} sudo cp /tmp/id_ed25519 /root/.ssh/id_ed25519', no_dry_run)

def data_exists(ctx):
    return _run(f"ssh {ctx.node} ls /lab/persistence/{ctx.namespace}/{ctx.deployment}", check=False).returncode == 0

def data_sync(ctx, src_node, target_node):
    src = f"/lab/persistence/{ctx.namespace}/{ctx.deployment}/"
    dst = f"{target_node}:/lab/persistence/{ctx.namespace}/{ctx.deployment}"
    rsync = 'rsync -avz --delete --rsync-path=\\"sudo rsync\\"'
    rsync_ssh = '-e \\"ssh -F /home/lab/.ssh/config\\"'

    ctx.info(f"backing up to {target_node}")
    dry(f'ssh -A {src_node} "sudo {rsync} {rsync_ssh} {src} lab@{dst}"', ctx.no_dry_run)

def _run(cmd, check=True, silent=False):
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=False)
    if not silent and res.returncode != 0:
        print(f"ran: {cmd}: {res.returncode}")
        print(f"stderr: {res.stdout}")
        print(f"stderr: {res.stderr}")
    if check and res.returncode != 0:
        raise Exception(f"cmd error {res.returncode}: '{cmd}'\n...stderr...\n{res.stdout}\n...stderr...\n{res.stderr}")
    return res

def dry(cmd, no_dry_run=True):
    if no_dry_run: _run(cmd)
    else: print(f"dry-run: {cmd}")

def out(cmd, check=True, silent=False):
    return _run(cmd, check=check, silent=silent).stdout.strip()

def wait_for_tasks(futures, error_msg):
    errors = []
    for f in futures:
        try: f.result()
        except Exception as e:
            print(f"[ERROR] {error_msg}: {e}\n{traceback.format_exc()}")
            errors.append(e)
    return errors