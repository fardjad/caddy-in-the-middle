#!/usr/bin/env bash

set -euo pipefail

apt-get update -y && apt-get install -y \
	build-essential \
	git \
	git-lfs \
	golang \
	jq \
	neovim \
	tmux \
	vim \
	zsh

chsh -s /bin/zsh $(whoami)

uv tool install black
uv tool install rust-just

# Go tools
go install github.com/google/yamlfmt/cmd/yamlfmt@latest
go install github.com/reteps/dockerfmt@latest
go install mvdan.cc/sh/v3/cmd/shfmt@latest

# Node.js 24.x
curl -fsSL https://deb.nodesource.com/setup_24.x | bash -
apt-get update
apt-get install -y --no-install-recommends nodejs

npm install -g dclint

# starship
curl -fsSL https://starship.rs/install.sh -o /tmp/install_starship.sh
chmod +x /tmp/install_starship.sh
/tmp/install_starship.sh -y
rm -f /tmp/install_starship.sh

# Docker
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc

tee /etc/apt/sources.list.d/docker.sources <<INEOF
Types: deb
URIs: https://download.docker.com/linux/debian
Suites: $(. /etc/os-release && echo "$VERSION_CODENAME")
Components: stable
Signed-By: /etc/apt/keyrings/docker.asc
INEOF

apt-get update -y
apt-get install -y docker-ce-cli docker-buildx-plugin docker-compose-plugin

export PATH="$HOME/.local/bin:$HOME/go/bin:$PATH"
mkdir -p "$HOME/.zsh/completion"
just --completions=zsh >"$HOME/.zsh/completion/_just"

cat >"$HOME/.zshrc" <<INEOF
export PATH="\$HOME/.local/bin:\$HOME/go/bin:\$PATH"

fpath=("\$HOME/.zsh/completion" \$fpath)
autoload -U compinit
compinit

eval "\$(starship init zsh)"
INEOF
