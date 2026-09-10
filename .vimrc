" ~/.vimrc -- shared by every machine this repo deploys to, so it has to work in
" older Vims (7.4+) and in terminal Vim under tmux, not just on the Mac.

set nocompatible    " a no-op when read as ~/.vimrc, but not under `vim -u`

let mapleader = '#'

" --- Appearance ------------------------------------------------------------

set background=dark
if &t_Co > 2 || has('gui_running')
  syntax on
  set hlsearch
endif
highlight Search cterm=NONE ctermfg=black ctermbg=yellow

set laststatus=2    " always show the status line
set showcmd         " also shows the size of a visual selection
set shortmess-=S    " show the match count, e.g. [3/12], when searching
set tabpagemax=40

" --- Editing ---------------------------------------------------------------

filetype plugin indent on

set expandtab softtabstop=4 shiftwidth=4 autoindent
set textwidth=0 wrapmargin=0    " never hard-wrap while typing
set hidden                      " switch buffers without saving first
set autoread                    " pick up files changed outside Vim
set pastetoggle=<F6>

let g:tex_flavor = 'latex'      " a .tex file is LaTeX, not plain TeX

let g:fortran_free_source = 1
let g:fortran_have_tabs = 1
let g:fortran_more_precise = 1
let g:fortran_do_enddo = 1

let g:NERDTreeIgnore = ['\.pyc$']

" Keeps the cursor and view where they were: a bare `%s/\s\+$//e` leaves the
" cursor on the last line it changed, so every save would jump.
function! StripTrailingWhitespaces() abort
  let l:view = winsaveview()
  keeppatterns %s/\s\+$//e
  call winrestview(l:view)
endfunction

" Rebuild ~/.vim/spell/*.add.spl whenever its .add word list is newer, so words
" added on one machine and synced through this repo work everywhere.
" https://vi.stackexchange.com/a/5052/21725
for s:add in glob('~/.vim/spell/*.add', 1, 1)
  if filereadable(s:add) &&
        \ (!filereadable(s:add . '.spl') || getftime(s:add) > getftime(s:add . '.spl'))
    silent execute 'mkspell! ' . fnameescape(s:add)
  endif
endfor
unlet! s:add

" --- Autocommands ----------------------------------------------------------
" All in one group that is cleared on entry, so re-sourcing this file replaces
" them instead of stacking up another copy of each.

augroup vimrc
  autocmd!

  autocmd BufRead,BufNewFile rose-*.conf,rose-*.info set filetype=rose-conf
  autocmd BufRead,BufNewFile *.conf setfiletype dosini

  autocmd FileType fortran setlocal shiftwidth=2 tabstop=2 softtabstop=2
  " Case-insensitive search in Fortran only. 'ignorecase' is global -- there is
  " no buffer-local copy, so `setlocal ic` would leave every other buffer
  " ignoring case too once a Fortran file had been opened. Switch it on the way
  " in and off the way out.
  autocmd BufEnter,FileType * if &filetype ==# 'fortran' | set ignorecase | endif
  autocmd BufLeave * if &filetype ==# 'fortran' | set noignorecase | endif

  autocmd FileType tex setlocal wrap linebreak textwidth=0 wrapmargin=0

  autocmd BufWritePre * if &filetype =~# '^\(python\|tex\)$'
        \ | call StripTrailingWhitespaces() | endif

  " F4: save and `remake run` the current Python file.
  autocmd FileType python
        \ nnoremap <buffer> <F4> :w<CR>:exec '!remake run' shellescape(@%, 1)<CR>
  autocmd FileType python
        \ inoremap <buffer> <F4> <Esc>:w<CR>:exec '!remake run' shellescape(@%, 1)<CR>

  " Pairs with 'autoread'. Skipped in the command-line window (q:), where
  " :checktime is not allowed and would raise E11.
  autocmd FocusGained,BufEnter,CursorHold,CursorHoldI *
        \ if getcmdwintype() ==# '' | checktime | endif
augroup END

" --- Mappings --------------------------------------------------------------

" H / L: previous / next buffer.
nnoremap H :bprevious<CR>
nnoremap L :bnext<CR>

" Ctrl-H / Ctrl-L: move the current tab one place left / right.
nnoremap <silent> <C-h> :silent! tabmove -1<CR>
nnoremap <silent> <C-l> :silent! tabmove +1<CR>

" In visual mode, / searches for the selected text, taken literally.
xnoremap / y/\V<C-R>=substitute(escape(@", '/\'), '\n', '\\n', 'g')<CR><CR>

" #s: toggle British-English spell checking (in insert mode, <C-o>#s).
nnoremap <Leader>s :setlocal spell! spelllang=en_gb<CR>

" Function keys. The Ctrl-Shift ones generally only fire in a GUI Vim: most
" terminals, and tmux, do not pass Ctrl-Shift-F<n> through as a distinct key.
nnoremap <F2> :NERDTreeToggle<CR>
nnoremap <F3> :!make<CR><CR>
nnoremap <C-S-F3> :!make clean<CR><CR>
" F4 is `remake run`, Python buffers only -- see the autocommands above.
nnoremap <F5> :edit!<CR>
nnoremap <S-F5> :tabdo edit!<CR>
" F6 is 'pastetoggle', set above.
" F7: open the citation under the cursor.
nnoremap <F7> "zyiw:exec '!litman display' shellescape(@z, 1) '2>/dev/null 1>/dev/null'<CR><CR>
" F8: grep for the word under the cursor into the quickfix list.
nnoremap <F8> :grep! "\<<cword>\>" . -r<CR>
" F9: grep for it into a new tab; Shift-F9 then opens the file named at the
" start of the line, at the first match.
nnoremap <F9> *N:execute 'tabnew <bar> r ! grep -ir --exclude=tags --exclude=\*.swp '.expand("<cword>")<CR><CR>
nnoremap <S-F9> ^<C-w>gfn
nnoremap <C-S-F9> ^<C-w>gfngT:q!<CR>
" F12: follow the tag under the cursor in a new tab.
nnoremap <silent> <F12> <C-w><C-]><C-w>T
