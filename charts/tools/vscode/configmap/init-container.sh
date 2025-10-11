apt install -fy ansible age
cd /workspace/homelab-machines/ansible
ansible-playbook -i inventory/vscode.ini site.yaml