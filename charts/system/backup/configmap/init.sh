#!/usr/bin/bash

apt update
apt install -fy python3 ssh curl

arch=$([ "$(uname -m)" == "x86_64" ] && echo amd64 || echo arm64)
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/$arch/kubectl"
