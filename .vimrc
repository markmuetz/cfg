" ~/.vimrc -- shared by every machine this repo deploys to, so it has to work in
" older Vims (7.4+) and in terminal Vim under tmux, not just on the Mac.
"
" Plugins are vendored into ~/.vim/pack/vendor/start/ by bin/vim-plugins, and
" need Vim 8+ (7.4 has no packages, so it just runs without them). The external
" tools some of them use -- rg, fzf, ruff -- are optional per machine: see
" notes/new_computer_setup.md.

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
if has('packages')
  packadd! matchit    " % also jumps if/else/endif, \begin/\end, tags...
endif

set expandtab softtabstop=4 shiftwidth=4 autoindent
set textwidth=0 wrapmargin=0    " never hard-wrap while typing
set hidden                      " switch buffers without saving first
set autoread                    " pick up files changed outside Vim
set pastetoggle=<F6>

" LaTeX via vimtex: \ll compiles (continuously), \lv views. See
" notes/install_latex.md.
let g:tex_flavor = 'latex'      " a .tex file is LaTeX, not plain TeX
let g:vimtex_compiler_latexmk = {'out_dir': '_build'}
" Only where latexmk exists. Otherwise vimtex warns on every .tex file, and its
" warning code crashes on Vim 9.1 (E684/E128 in vimtex#debug#stacktrace, still
" present in v2.18), so you get an error instead of the message.
let g:vimtex_compiler_enabled = executable('latexmk')
let g:vimtex_syntax_nospell_comments = 1

let g:fortran_free_source = 1
let g:fortran_have_tabs = 1
let g:fortran_more_precise = 1
let g:fortran_do_enddo = 1

" Python linting as you type, via ALE + ruff (does nothing where ruff is not
" installed). :ALEFix applies ruff's fixes and formatting on demand -- not on
" save, where reformatting a whole existing file would bury the real change.
let g:ale_linters = {'python': ['ruff']}
let g:ale_fixers = {'python': ['ruff', 'ruff_format']}

" F2's file tree is Vim's built-in netrw.
let g:netrw_liststyle = 3       " tree view
let g:netrw_winsize = 25        " % of the width, rather than half the screen
let g:netrw_list_hide = '\.pyc$'
let g:netrw_dirhistmax = 0      " no ~/.vim/.netrwhist: it is inside the cfg work tree

" Search with ripgrep where installed: much faster, and skips what .gitignore
" does. Plain grep otherwise -- not every machine has rg.
if executable('rg')
  set grepprg=rg\ --vimgrep
  set grepformat=%f:%l:%c:%m
  " fzf's :Files too, unless the shell already chose its source.
  if empty($FZF_DEFAULT_COMMAND)
    let $FZF_DEFAULT_COMMAND = 'rg --files'
  endif
endif

" fzf.vim (:Files, :Rg, :Buffers, ...) only where the fzf binary exists.
" Elsewhere its commands would offer to download fzf into ~/.vim.
if has('packages') && executable('fzf')
  packadd fzf
  packadd fzf.vim
endif

" F9's results go in one scratch buffer, replaced by each new F9. It is
" unlisted, so H / L skip it, but kept when hidden, so after opening a result
" <C-^> comes back to it.
function! s:GrepToBuffer(word) abort
  if executable('rg')
    let l:cmd = 'rg -i --sort=path --glob ' . shellescape('!tags')
  else
    let l:cmd = 'grep -ir --exclude=tags --exclude=' . shellescape('*.swp')
  endif
  let l:old = get(s:, 'grep_buf', -1)
  enew
  setlocal buftype=nofile bufhidden=hide noswapfile nobuflisted
  if l:old != bufnr('') && bufexists(l:old)
    execute 'bwipeout' l:old
  endif
  let s:grep_buf = bufnr('')
  " Switching back into a buffer (<C-^>, :b) lists it again; undo that.
  augroup vimrc
    autocmd BufEnter <buffer> setlocal nobuflisted
  augroup END
  call setline(1, systemlist(l:cmd . ' -- ' . shellescape(a:word) . ' .'))
  " Enter does what Shift-F9 does. Shift-F9 depends on the terminal sending
  " xterm's code for it, which not all do (e.g. Terminal.app).
  nnoremap <buffer> <CR> :call <SID>OpenGrepResult(0)<CR>
endfunction

" Open the file named at the start of the line, at the first match of the
" search F9 set. With a:close, also discard F9's results buffer.
function! s:OpenGrepResult(close) abort
  let l:from = bufnr('')
  normal! ^gf
  silent! normal! n
  if a:close && l:from == get(s:, 'grep_buf', -1)
    execute 'bwipeout' l:from
  endif
endfunction

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
nnoremap <F2> :Lexplore<CR>
nnoremap <F3> :!make<CR><CR>
nnoremap <C-S-F3> :!make clean<CR><CR>
" F4 is `remake run`, Python buffers only -- see the autocommands above.
nnoremap <F5> :edit!<CR>
nnoremap <S-F5> :tabdo edit!<CR>
" F6 is 'pastetoggle', set above.
" F7: open the citation under the cursor.
nnoremap <F7> "zyiw:exec '!litman display' shellescape(@z, 1) '2>/dev/null 1>/dev/null'<CR><CR>
" F8: grep for the word under the cursor into the quickfix list.
if executable('rg')
  nnoremap <F8> :grep! -w -- <cword> .<CR>
else
  nnoremap <F8> :grep! "\<<cword>\>" . -r<CR>
endif
" F9: grep for it, case-insensitively, into a scratch buffer; Enter (or
" Shift-F9) on a result then opens that file, at the first match, and <C-^>
" returns to the results. Ctrl-Shift-F9 opens it and discards the results.
nnoremap <F9> *N:call <SID>GrepToBuffer(expand('<cword>'))<CR>
nnoremap <S-F9> :call <SID>OpenGrepResult(0)<CR>
nnoremap <C-S-F9> :call <SID>OpenGrepResult(1)<CR>
" F12: follow the tag under the cursor in a new tab.
nnoremap <silent> <F12> <C-w><C-]><C-w>T
