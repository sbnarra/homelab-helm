

/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"
brew tap Homebrew/bundle

cd /static
brew bundle

cd /workspace/home-lab

tgenv install
tfenv install
tfenv use

chown -R abc:abc /home/linuxbrew/.linuxbrew

mkdir -p /etc/ansible
echo "[ssh_connection]
control_path_dir=/dev/shm/ansible_control_path" >> /etc/ansible/ansible.cfg

helm plugin install https://github.com/databus23/helm-diff
