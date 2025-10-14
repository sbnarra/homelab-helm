import subprocess
import traceback
import env

def setup_ssh(nodes):
    run(f"eval $(ssh-agent -s) && ssh-add /root/.ssh/id_ed25519")
    for node in nodes: # required for rsync
        dry(f'scp /root/.ssh/id_ed25519 {node}:/tmp/id_ed25519')
        dry(f'ssh {node} sudo cp /tmp/id_ed25519 /root/.ssh/id_ed25519')

def run(cmd, check=True, silent=False):
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=False)
    if not silent and res.returncode != 0:
        print(f"ran: {cmd}: {res.returncode}")
        print(f"stderr: {res.stdout}")
        print(f"stderr: {res.stderr}")
    if check and res.returncode != 0:
        raise Exception(f"cmd error {res.returncode}: '{cmd}'\n...stderr...\n{res.stdout}\n...stderr...\n{res.stderr}")
    return res

def dry(cmd):
    if env.no_dry_run: run(cmd)
    else: print(f"dry-run: {cmd}")

def out(cmd, check=True, silent=False):
    return run(cmd, check=check, silent=silent).stdout.strip()

def wait_for_tasks(futures, error_msg):
    errors = []
    for f in futures:
        try: f.result()
        except Exception as e:
            print(f"[ERROR] {error_msg}: {e}\n{traceback.format_exc()}")
            errors.append(e)
    return errors