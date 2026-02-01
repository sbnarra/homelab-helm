install_deps() {
  apt-get install -fy --fix-missing \
    git vim sshpass zsh build-essential wget
    #  pkg-config libssl-dev
}

setup_config() {
  cp -a /static/ssh/* /config/.ssh/.
  chown abc:abc /config/.ssh/*

  for rc in .zshrc .bashrc .rc; do
    cp /static/files/$rc /config/$rc
    chown abc:abc /config/$rc
  done

  mkdir -p /docker
  chown -R abc:abc /docker
}

install_deps_retry() {
  cur=$(($1 - 1))
  install_deps
  if [ "$?" == "0" ]; then
    return
  else
    apt-get --fix-broken install
    sleep 10 && install_deps_retry $cur
  fi
}

install_go() {
  set -e
  wget -q -O /go1.23.5.linux-arm64.tar.gz https://go.dev/dl/go1.23.5.linux-arm64.tar.gz
  tar -C /usr/local -xzf /go1.23.5.linux-arm64.tar.gz
  # go install -v golang.org/x/lint/golint@latest
  /usr/local/go/bin/go install honnef.co/go/tools/cmd/staticcheck@latest
  chown -R abc:abc /usr/local/go
  set +e
}

configure_git() {
  git config --global user.name "lab"
  git config --global user.email "lab@vscode"
  git config --global --add safe.directory '*'
  git config --global init.defaultBranch main
}

brew_install() {
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"
  brew tap Homebrew/bundle

  cd /static/files
  brew bundle

  cd /workspace/homelab/deployments

  tgenv install
  tfenv install
  tfenv use

  chown -R abc:abc /home/linuxbrew/.linuxbrew
}

brew_background_install() {
  brew install ansible openapi-generator
  mkdir -p /etc/ansible
  echo "[ssh_connection]\ncontrol_path_dir=/dev/shm/ansible_control_path" >> /etc/ansible/ansible.cfg
  helm plugin install https://github.com/databus23/helm-diff
}

install_rust() {
  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
  cargo install espup --locked
  espup install
}

main() {
  setup_config
  apt-get update
  install_deps_retry 3
  configure_git &
  install_go &
  brew_install &
  wait
  
  brew_background_install &
  install_rust &
}

main