#!/bin/sh

#TODO: only use gvim for text files
#else open items parent

# View whitespace using [g]vim syntax highlighting
# Pass -g option to use gvim, otherwise vim is used
# Note one can pass - to read stdin

if [ "$1" = "-g" ]; then
    vim="gvim" #maybe -f to not fork?
    shift
else
    vim="vim"
fi

if [ "$#" = "1" ]; then
    if [ -d "$1" ]; then
        xdg-open "$1"
        exit
    fi
fi

if ! $vim -h >/dev/null 2>&1; then
    cat >/dev/null #to stop xargs warning
    echo "Error: please install $vim to view whitespace" >&2
    exit
fi

$vim -R \
+'highlight RedundantSpaces term=standout ctermbg=red guibg=red' \
+'match RedundantSpaces /\s\+$\| \+\ze\t/' \
+'set listchars=tab:>-,trail:.,extends:>' \
+'set list!' "$@"
