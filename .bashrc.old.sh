# if the command-not-found package is installed, use it
# if [ -x /usr/lib/command-not-found ]; then
#     function command_not_found_handle {
#         # check because c-n-f could've been removed in the meantime
#         if [ -x /usr/lib/command-not-found ]; then
#             /usr/bin/python /usr/lib/command-not-found -- $1
#             return $?
#         else
#             return 127
#         fi
#     }
# fi

# if [ $(echo $HOSTNAME|cut -c1-7) != "eslogin" ]; then
#     # Make these very large so that history-search-backwards has a lot of cmds.
#     export HISTSIZE=1000000
# fi

# alias jasmin-login1='echo -ne "\033]0;JASMIN-LOGIN1\007"; ssh -AY mmuetz@jasmin-login1.ceda.ac.uk'
# N.B. you can log in to jasmin2 from anywhere.
# alias jasmin-login2='echo -ne "\033]0;JASMIN-LOGIN2\007"; ssh -AY mmuetz@JasminLogin2'
# alias jasmin='echo -ne "\033]0;JASMIN\007"; ssh -o "ProxyCommand ssh -AY markmuetz@puma.nerc.ac.uk -W %h:%p" -AY mmuetz@jasmin-login1.ceda.ac.uk'

alias archer='echo -ne "\033]0;ARCHER\007"; ssh -Y mmuetz@login.archer.ac.uk'
# alias rdf='echo -ne "\033]0;RDF\007"; ssh -Y mmuetz@login.rdf.ac.uk'
alias puma='echo -ne "\033]0;PUMA\007"; ssh -Y markmuetz@puma.nerc.ac.uk'
# alias oak='echo -ne "\033]0;OAK\007"; ssh -Y hb865130@oak.reading.ac.uk'
# alias monsoon='echo -ne "\033]0;MONSOON\007"; ssh -Y mamue@lander.monsoon-metoffice.co.uk'
# alias jsync='rsync -e "ssh -o \"ProxyCommand ssh -A markmuetz@puma.nerc.ac.uk -W %h:%p\""'

# export JASMIN="mmuetz@jasmin-xfer1.ceda.ac.uk"
# export ARCHER="mmuetz@login.archer.ac.uk"

# Computer specific settings at end so can overwrite.
if [ $(echo $HOSTNAME|cut -c1-7) = "eslogin" ] || [ $(echo $HOSTNAME|cut -c1-6) = "esPP00" ] ; then
    # Interactive shells on ARCHER. 
    alias qserial='qsub -IVl select=serial=true:ncpus=1,walltime=10:0:0 -A n02-REVCON'
    # N.B.
    alias qshort='echo "REM aprun"; qsub -q short -IVl select=1,walltime=0:20:0 -A n02-REVCON'
    # export OMNIUM_ANALYSIS_PKGS=scaffold:cosar
    export WORK=/work/n02/n02/mmuetz
    export COSAR_SUITE_UAU197_DIR=/home/n02/n02/mmuetz/work/omnium_test_suites/cosar_test_suite/u-au197
    export SCAFFOLD_SUITE_UAN388_DIR=/home/n02/n02/mmuetz/work/omnium_test_suites/scaffold_test_suite/u-an388
    export ube530=/home/n02/n02/mmuetz/nerc/um11.0_runs/archive/u-be530
fi

if [ $HOSTNAME = "puma" ]; then
    . mosrs-setup-gpg-agent
    # N.B. different git location.
    # alias dotfiles='/usr/local/bin/git --git-dir=$HOME/.dotfiles/ --work-tree=$HOME'
fi

if [ $HOSTNAME = "zerogravitas" ]; then
    export PATH="/home/markmuetz/opt/MO/fcm-2016.12.0/bin:/home/markmuetz/opt/MO/cylc/bin:/home/markmuetz/opt/MO/rose-2017.01.0/bin:/home/markmuetz/opt/intel/bin:$PATH"
    # export OMNIUM_ANALYSIS_PKGS=scaffold:cosar
    export COSAR_SUITE_UAU197_DIR=/home/markmuetz/omnium_test_suites/cosar_test_suite/u-au197
    export SCAFFOLD_SUITE_UAN388_DIR=/home/markmuetz/omnium_test_suites/scaffold_test_suite/u-an388
    export ube530=/home/markmuetz/mirrors/archer/nerc/um11.0_runs/archive/u-be530/
    source $HOME/.anaconda3_setup.sh
fi

if [ $HOSTNAME = "breakeven" ]; then
    . $HOME/.argcomplete.rc
    export PATH="/home/markmuetz/opt/fcm-2016.05.1/bin:/home/markmuetz/opt/cylc-6.10.2/bin:/home/markmuetz/opt/rose-master/bin:$PATH"
    # export OMNIUM_ANALYSIS_PKGS=scaffold:cosar
    export OMNIUM_ANALYSIS_PKGS=cosar
    export ube530=/home/markmuetz/mirrors/archer/nerc/um11.0_runs/archive/u-be530/
fi 
if [ $HOSTNAME = "exppostproc01.monsoon-metoffice.co.uk" ]; then
    export OMNIUM_ANALYSIS_PKGS=scaffold:cosar
fi
if [ $HOSTNAME = "exvmsrose.monsoon-metoffice.co.uk" ]; then
    . mosrs-setup-gpg-agent
fi


