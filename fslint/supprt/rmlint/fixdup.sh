#!/bin/sh
# Does the same as the python version only slower.
# Systems without python can therefore use this.

suffix=.fixdup.$$

keepfile=''
while read file; do
  if [ -z "$file" ]; then
    keepfile="nextfile"
  elif [ "nextfile" = "$keepfile" ]; then
    keepfile="$file"
  else
    ln -f -b --suffix="$suffix" -- "$keepfile" "$file" 2>/dev/null ||
    ln -sf -b --suffix="$suffix" -- "$keepfile" "$file"
    rm -f "$file$suffix"
  fi
done
