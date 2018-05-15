" Set line width to 100 chars and turn on spelling.
" setlocal tw=100
" setlocal spell spelllang=en_gb

" N.B. Should be copied to ~/.vim/plugin/
let g:Tex_Outdir='_build' 

" Custom python prog that appends g:Tex_Outdir to the pdf's path before
" calling evince.
let g:Tex_ViewRule_pdf='vimsuite_pdf_viewer.py '.g:Tex_Outdir

" Move all output files to a separate dir.
let g:Tex_CompileRule_pdf = 'latexmk -pdf -output-directory='.g:Tex_Outdir.' $*'
let g:Tex_DefaultTargetFormat = 'pdf'

" Start off with everything unfolded.
let Tex_FoldedSections=""
let Tex_FoldedEnvironments=""
let Tex_FoldedMisc=""
