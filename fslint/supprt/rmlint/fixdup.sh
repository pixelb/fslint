#!/bin/sh
# Does the same as the python version only slower.
# Systems without python can therefore use this.

suffix=.fixdup.$$

link=1
dryRun=0
if [ "$#" = "1" ]; then
    if [ "$1" = "del" ]; then
        link=0
    elif [ "$1" = "tdel" ]; then
        link=0
        dryRun=1
    elif [ "$1" = "tmerge" ]; then
        dryRun=1
    fi
fi

keepfile='nextfile'
while read file; do
  if [ -z "$file" ]; then
    keepfile="nextfile"
  elif [ "nextfile" = "$keepfile" ]; then
    keepfile="$file"
    if [ "$dryRun" = "1" ]; then
        printf "\n\nkeeping:     $keepfile\n"
        if [ "$link" = "1" ]; then
            printf "hardlinking: "
        else
            printf "deleting: "
        fi
    fi
  else
    if [ "$dryRun" = "1" ]; then
        printf "$file "
    else
        if [ "$link" = "1" ]; then
            ln -f -b --suffix="$suffix" -- "$keepfile" "$file" 2>/dev/null ||
            ln -sf -b --suffix="$suffix" -- "$keepfile" "$file"
            rm -f "$file$suffix"
        else
            rm -f "$file"
        fi
    fi
  fi
done
if [ "$dryRun" = "1" ] && [ "$keepfile" != "nextfile" ]; then
    echo
fi
