" Syntax highlighting for siunitx
" Very simple, commands copied from /usr/share/vim/vim74/syntax/tex.vim
" Using ideas from: https://tex.stackexchange.com/a/427412/42834
" and: https://tex.stackexchange.com/a/412867/42834
" Not sure if I have done it correctly, but it works.
" Makes \SI and \si act as maths zones.

syn region texMathZoneZ	matchgroup=texStatement start="\\SI{"	matchgroup=texStatement	end="}"		end="%stopzone\>"	contains=@texMathZoneGroup
syn region texMathZoneZ	matchgroup=texStatement start="\\SI{.\{-}}{"	matchgroup=texStatement	end="}"		end="%stopzone\>"	contains=@texMathZoneGroup
syn region texMathZoneZ	matchgroup=texStatement start="\\si{"	matchgroup=texStatement	end="}"		end="%stopzone\>"	contains=@texMathZoneGroup
