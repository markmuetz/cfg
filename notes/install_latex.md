Installing LaTeX
================

Nothing to do on the Vim side: vimtex is vendored into
`~/.vim/pack/vendor/start/` by this repo (see `bin/vim-plugins`), so it arrives
with `cfg-install`. It needs a TeX distribution with `latexmk` on the machine.
Without `latexmk`, `.vimrc` switches vimtex's compiler off -- editing, syntax
and motions still work, but `\ll` does nothing.

macOS:

    brew install --cask mactex-no-gui    # full TeX Live, several GB
    # or a minimal base, adding packages as documents need them:
    brew install --cask basictex && sudo tlmgr install latexmk

Debian/Ubuntu:

    sudo apt install latexmk texlive-latex-extra texlive-science texlive-bibtex-extra biber texlive-fonts-recommended

Using it -- vimtex's default keys, with `\` as the local leader:

    \ll    start/stop continuous compilation (latexmk); output goes to _build/
    \lv    view the PDF (macOS: `open`, i.e. Preview; Linux: xdg-open)
    \le    errors and warnings in the quickfix window
    \lc    clean the auxiliary files
    \lt    table of contents
    #s     toggle spell check (en_gb) -- this one is from .vimrc

Plus text objects and edits that understand LaTeX: `ie`/`ae` (environment),
`i$`/`a$` (maths), `cse` / `dse` (change / delete the surrounding
environment), `]]` / `[[` (next / previous section). `:help vimtex` for the rest.

Preview does not reload a PDF that changes under it; Skim does, and vimtex
supports it with `let g:vimtex_view_method = 'skim'`.
