[[ $0 != "$BASH_SOURCE" ]] && SOURCED=1 || SOURCED=0

if [ "$SOURCED" == 0 ]; then
    echo MUST BE SOURCED
    exit 1
fi

NEXT_SV=${1:-"next thursday"}

DAYOFWEEK=$(date -d"${NEXT_SV}" +"%u")
if [ "$DAYOFWEEK" == 4 ];  then    
    # It's a Thursday.
    export SV=$HOME/Dropbox/PhD/SV/`date -d"${NEXT_SV}" +"%Y%m%d"`
    echo "export SV=$SV"
    if [ ! -d "$SV" ]; then
        echo "mkdir -p $SV"
        mkdir -p $SV
    fi
else    
    echo Not a Thursday! 
    # Don't exit here or it will close your terminal!
fi
