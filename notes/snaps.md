Installing snaps:

    # sudo apt install snapd
    # No idea why this works??
    sudo apt purge snapd snap-confine && sudo apt install -y snapd
    sudo snap install pycharm-professional


    # Either:
    snap run pycharm-professional
    # or:
    export PATH=$PATH:/snap/bin
    pycharm-professional
