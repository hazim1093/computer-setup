##############################
##############################
# Own config 
##############################
##############################

# My config for p10k
source /usr/local/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
ZSH_TMUX_AUTOSTART='true'
export PATH="/usr/local/opt/m4/bin:$PATH"

export POWERLEVEL9K_KUBECONTEXT_SHOW_ON_COMMAND='kubectl|helm|kubens|kubectx|kctx|kns|k|kubecolor'
export POWERLEVEL9K_GCLOUD_SHOW_ON_COMMAND='gcloud|gcs|gsutil'

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

alias kctx=kubectx
alias kns=kubens

# Helm
source <(helm completion zsh)

# Flux
command -v flux >/dev/null && . <(flux completion zsh)
##########################################################################

# Docker / lima
alias d="lima nerdctl"

# Google cloud
source "$(brew --prefix)/Caskroom/google-cloud-sdk/latest/google-cloud-sdk/completion.zsh.inc"
export USE_GKE_GCLOUD_AUTH_PLUGIN=True

# Node
  export NVM_DIR="$HOME/.nvm"
  [ -s "/usr/local/opt/nvm/nvm.sh" ] && \. "/usr/local/opt/nvm/nvm.sh"  # This loads nvm
  [ -s "/usr/local/opt/nvm/etc/bash_completion.d/nvm" ] && \. "/usr/local/opt/nvm/etc/bash_completion.d/nvm"  # This loads nvm bash_completion

# Go
export GOBIN="$HOME/go/bin"
export PATH=$PATH:$GOBIN

[ -f ~/.fzf.zsh ] && source ~/.fzf.zsh

autoload -U copy-earlier-word
zle -N copy-earlier-word
bindkey '\e\e.' copy-earlier-word

autoload -U +X bashcompinit && bashcompinit
complete -o nospace -C /usr/local/bin/terraform terraform

### MANAGED BY RANCHER DESKTOP START (DO NOT EDIT)
export PATH="/Users/ext.hazim.malik/.rd/bin:$PATH"
### MANAGED BY RANCHER DESKTOP END (DO NOT EDIT)
