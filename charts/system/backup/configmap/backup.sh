#!/usr/bin/bash

apt-get update && apt-get install -fy \
    python3 ssh curl

arch=$([ "$(uname -m)" == "x86_64" ] && echo amd64 || echo arm64)
curl -L "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/$arch/kubectl" \
  -o /usr/local/bin/kubectl
chmod +x /usr/local/bin/kubectl

cat /id_ed25519
ls -l /id_ed25519

python3 /backup.py --max-jobs 8