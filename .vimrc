
" An example for a vimrc file. 

" Maintainer: Bram Moolenaar 
" Last change: 2002 May 28 
 
" To use it, copy it to 
" for Unix and OS/2: ~/.vimrc 
" for Amiga: s:.vimrc 
" for MS-DOS and Win32: $VIM\_vimrc 
" for OpenVMS: sys$login:.vimrc 

" When started as "evim", evim.vim will already have done these settings. 
"if v:prognAme =~? "evim" 
" finish 
"endif 

" Use Vim settings, rather then Vi settings (much better!). 
" This must be first, because it changes other options as a side effect. 
set nocompatible 
" " allow backspacing over everything in insert mode 
" set backspace=indent,eol,start 
"
" set autoindent " always set autoindenting on 
" "if has("vms") 
" set nobackup " do not keep a backup file, use versions instead 
" "else 
" " set backup " keep a backup file 
" "endif 
" set history=50 " keep 50 lines of command line history 
" set ruler " show the cursor position all the time 
" set showcmd " display incomplete commands 
" set incsearch " do incremental searching 
"
" " For Win32 GUI: remove 't' flag from 'guioptions': no tearoff menu entries 
" " let &guioptions = substitute(&guioptions, "t", "", "g") 
"
" " Don't use Ex mode, use Q for formatting 
" map Q gq 
"
" " This is an alternative that also works in block mode, but the deleted 
" " text is lost and it only works for putting the current register. 
" "vnoremap p "_dp 
"
" " Switch syntax highlighting on, when the terminal has colors 
" " Also switch on highlighting the last used search pattern. 
if &t_Co > 2 || has("gui_running") 
 syntax on 
 set hlsearch 
endif 
"
"   " Only do this part when compiled with support for autocommands. 
"   if has("autocmd") 
"
"   " Enable file type detection. 
"   " Use the default filetype settings, so that mail gets 'tw' set to 72, 
"   " 'cindent' is on in C files, etc. 
"   " Also load indent files, to automatically do language-dependent
"   indenting. 
"   filetype plugin indent on 
"
"   " For all text files set 'textwidth' to 78 characters. 
"   autocmd FileType text setlocal textwidth=78 
"
"   endif
"

" set tabs to space, instead of tabs. Set defauly indent to 2
set softtabstop=4
set sw=4
set autoindent
set expandtab
filetype plugin indent on

" when using visual select, pressing / searches for selected text
vmap / y/<C-R>"<CR>

"imap <c-q> <esc>
"imap <c-s> <Esc><c-s>
" map! ;; <Esc> 
map <S-h> gT
map <S-l> gt
nnoremap <silent> <C-h> :execute 'silent! tabmove ' . (tabpagenr()-2)<CR>
" nnoremap <C-h> :execute 'tabmove ' . (tabpagenr()-2)<CR>
nnoremap <silent> <C-l> :execute 'silent! tabmove ' . (tabpagenr()+1)<CR>
" nnoremap <C-l> :execute 'tabmove ' . (tabpagenr()+1)<CR>
" map <C-S-h> gT
" map <C-S-l> gt
" map <S-l> :cnext<CR>
" map <S-h> :cprev<CR>
" Awesome plugin support
map <F2> :NERDTreeToggle<CR>
" Ignore *.pyc in nerdtree:
let NERDTreeIgnore = ['\.pyc$']

" For those with sadly no function keys available
" " toggle spelling use \s
imap <Leader>s <C-o>:setlocal spell! spelllang=en_gb<CR>
nmap <Leader>s :setlocal spell! spelllang=en_gb<CR>

" Enable rose syntax highlighting.
augroup filetype
  au! BufRead,BufnewFile rose-*.conf,rose-*.info set filetype=rose-conf
augroup END

" Fortran files:
autocmd FileType fortran :setlocal sw=2 ts=2 sts=2 " Two spaces for fortran files 

" Tags options.
" Recurse up looking for tags.
set tags=./tags;/
" F12 - open in new tab.
nnoremap <silent><F12> <C-w><C-]><C-w>T

" Easy search for word under cursor.
nnoremap <F8> :grep! "\<<cword>\>" . -r<CR>
" Search and store results in a new tab, also selects searched for word.
nnoremap <F9> *N:execute 'tabnew <bar> r ! grep -ir --exclude=tags --exclude=\*.swp '.expand("<cword>")<CR><CR>
" Open the filename (at start of line), jump to first instance of word
nnoremap <S-F9> ^<C-w>gfn
nnoremap <C-S-F9> ^<C-w>gfngT:q!<CR>
" nnoremap <C-F10> :q!<CR>^<C-w>gfn
"
nnoremap <F5> :edit!<CR>
" Not working properly.
nnoremap <S-F5> :tabdo edit! | $ 

set pastetoggle=<F6>

:autocmd BufRead,BufNewFile *.conf setf dosini
set tw=0

hi Search cterm=NONE ctermfg=black ctermbg=yellow
set tabpagemax=40
