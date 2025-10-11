cp -a /static/.ssh/* /config/.ssh/.
chown abc:abc /config/.ssh/*

for rc in .zshrc .bashrc .rc; do
  cp /static/$rc /config/$rc
  chown abc:abc /config/$rc
done

mkdir -p /docker
chown -R abc:abc /docker