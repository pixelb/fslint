#!/bin/sh
# Does the same as the python version only slower.
# Systems without python can therefore use this.

keepfile=''
while read file; do
  if [ -z "$file" ]; then
    keepfile="nextfile"
  elif [ "nextfile" = "$keepfile" ]; then
    keepfile="$file"
  else
    ln -f -- "$keepfile" "$file"
  fi
done
