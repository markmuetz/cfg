set runtimepath^=~/.vim runtimepath+=~/.vim/after
let &packpath = &runtimepath
source ~/.vimrc

call plug#begin('~/.config/nvim/plugged')

Plug 'numirias/semshi', {'do': ':UpdateRemotePlugins'}

call plug#end()
