# Use: source ~/.setup_cosmic_mtg.sh [today]
[[ $0 != "$BASH_SOURCE" ]] && SOURCED=1 || SOURCED=0

if [ "$SOURCED" == 0 ]; then
    echo MUST BE SOURCED
    exit 1
fi

NEXT_MTG=${1:-"next tuesday"}

DAYOFWEEK=$(date -d"${NEXT_MTG}" +"%u")
if [ "$DAYOFWEEK" == 2 ];  then    
    # It's a Tuesday.
    export COSMICMTG=$HOME/Dropbox/COSMIC/Meetings/`date -d"${NEXT_MTG}" +"%Y%m%d"`
    echo "export COSMICMTG=$COSMICMTG"
    if [ ! -d "$COSMICMTG" ]; then
        echo "mkdir -p $COSMICMTG"
        mkdir -p $COSMICMTG
    fi

    echo "set up cosmic_sync"
    cosmic_sync() {
        rsync -Rav "$@" $COSMICMTG
    }
else    
    echo Not a Tuesday! 
    # Don't exit here or it will close your terminal!
fi
