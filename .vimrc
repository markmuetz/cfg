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
"
let mapleader = '#'

" set tabs to space, instead of tabs. Set defauly indent to 2
set softtabstop=4
set sw=4
set autoindent
set expandtab
filetype plugin indent on

" when using visual select, pressing / searches for selected text
vmap / y/<C-R>"<CR>

:set hidden
"imap <c-q> <esc>
"imap <c-s> <Esc><c-s>
" map! ;; <Esc> 
map <S-h> :bp<CR>
map <S-l> :bn<CR>
nnoremap <silent> <C-h> :execute 'silent! tabmove ' . (tabpagenr()-2)<CR>
" Is this right on all computers? Try +1 if not.
nnoremap <silent> <C-l> :execute 'silent! tabmove ' . (tabpagenr()+1)<CR>

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

augroup filetype
  au! BufRead,BufnewFile *.tex set filetype=tex
augroup END

" Fortran files:
" Two spaces for fortran files and ignore case on search.
autocmd FileType fortran :setlocal sw=2 ts=2 sts=2 ic
let fortran_free_source=1
let fortran_have_tabs=1
let fortran_more_precise=1
let fortran_do_enddo=1

autocmd FileType tex :setlocal wrap linebreak tw=0 wrapmargin=0

" Tags options.
" Recurse up looking for tags.
" set tags=./tags;/
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

" Visual select will show how many chars selected.
set sc

" stop vim autowrapping.
set textwidth=0 wrapmargin=0

set laststatus=2

fun! StripTrailingWhitespaces()
    let l = line(".")
    let c = col(".")
    %s/\s\+$//e
    call cursor(l, c)
endfun

nnoremap <F3> :!make <enter><enter>
" Not working? What's up with ctrl + F<number>?
nnoremap <C-S-F3> :!make clean <enter><enter>
" Activate vim help for word under cursor.
nnoremap <F4> "zyiw:exe "h ".@z.""<CR>
" Open citation for word under cursor.
nnoremap <F7> "zyiw:exec '!litman display' shellescape(@z, 1) '2>/dev/null 1>/dev/null'<CR><CR>

" Regenerate binary file ~/.vim/spell/en.utf-8.add.spl every time vim starts
" IF it is newer than the corresponding .add file.
" https://vi.stackexchange.com/a/5052/21725
for d in glob('~/.vim/spell/*.add', 1, 1)
    if filereadable(d) && (!filereadable(d . '.spl') || getftime(d) > getftime(d . '.spl'))
        silent exec 'mkspell! ' . fnameescape(d)
    endif
endfor

autocmd FileType tex autocmd BufWritePre <buffer> %s/\s\+$//e
autocmd FileType python autocmd BufWritePre <buffer> %s/\s\+$//e
