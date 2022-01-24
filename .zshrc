##############################
##############################
# Own config 
##############################
##############################

# My config for p10k
source /usr/local/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
ZSH_TMUX_AUTOSTART='true'
export PATH="/usr/local/opt/m4/bin:$PATH"

# terminal left right
bindkey "\e\e[D" backward-word
bindkey "\e\e[C" forward-word

# SSH Agent
[ -z "$SSH_AUTH_SOCK" ] && eval "$(ssh-agent -s)"

# Python
eval "$(pyenv init --path)"

# Env variables
PATH=${PATH}:~/Tools/own-bin

#########################################################################
# Kubernetes
#########################################################################
# Kubectl
[[ /usr/local/bin/kubectl ]] && source <(kubectl completion zsh)
alias kubectl="kubecolor"
command -v kubecolor >/dev/null 2>&1 && alias kubectl="kubecolor"

# make completion work with kubecolor
compdef kubecolor=kubectl

alias k=kubectl
complete -F __start_kubectl k

# Helm
source <(helm completion zsh)

# Flux
command -v flux >/dev/null && . <(flux completion zsh)
##########################################################################

# Nvm
export NVM_DIR="$HOME/.nvm"
[ -s "/usr/local/opt/nvm/nvm.sh" ] && . "/usr/local/opt/nvm/nvm.sh"  # This loads nvm
[ -s "/usr/local/opt/nvm/etc/bash_completion.d/nvm" ] && . "/usr/local/opt/nvm/etc/bash_completion.d/nvm"  # This loads nvm bash_completion
