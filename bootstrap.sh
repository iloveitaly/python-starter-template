###############################
# Bootstrap Agent Environments
###############################

# mise setup
curl https://mise.run | sh
mise trust

export MISE_ENV=dev,extras
mise install

source <(mise activate)

# zsh and ssl cert stuff for localias
sudo apt update && sudo apt install -y zsh libnss3-tools

# mise must be setup first!
echo 'eval "$(mise activate bash)"' >> ~/.bashrc
echo 'eval "$(direnv hook bash)"' >> ~/.bashrc

cat << 'EOF' >> ~/.bashrc

###################################
# Mise & Direnv Setup
# Assumes `mise use -g direnv@latest just@latest`
###################################

# mise first, then direnv, to ensure paths are set correctly before direnv takes a snapshot of env
eval "$(mise activate bash)"
eval "$(direnv hook bash)"

# nice to haves, like tab justfile completion
eval "$(just --completions $(basename "$SHELL"))"

###################################
# End Mise & Direnv Setup
###################################

EOF

# just up w/docker login information?
