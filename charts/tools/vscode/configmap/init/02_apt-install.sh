
install_deps() {
  apt update --fix-missing && \
    apt install -fy git vim sshpass zsh build-essential wget
}

install_deps_retry() {
  cur=$(($1 - 1))
  install_deps
  if [ "$?" == "0" ]; then
    return
  else
    sleep 10 && install_deps_retry $cur
  fi
}

install_deps_retry 3

git config --global user.name "lab"
git config --global user.email "lab@vscode"
git config --global --add safe.directory '*'
git config --global init.defaultBranch main

set -e
wget -q -O /go1.23.5.linux-amd64.tar.gz https://go.dev/dl/go1.23.5.linux-amd64.tar.gz
tar -C /usr/local -xzf /go1.23.5.linux-amd64.tar.gz
chown -R abc:abc /usr/local/go
set +e
