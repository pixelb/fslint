#!/bin/sh

set -e #exit on error

usage() {
    echo "Usage: `basename $0`: --eol|'' --indent-spaces|--indent-tabs|'' indent_width filename" >&2
    exit 1
}

[ "$#" == "4" ] || usage

FILE="$4"
if [ ! -f "$FILE" ]; then
    echo "Error: '$FILE' is not a regular file" >&2
    exit 1
fi


#Use cmp if available
cmp /dev/null /dev/null 2>/dev/null && CMP=cmp || CMP=false

TMP=${TMPDIR:-/tmp}
TMP="$TMP/fix_ws.$$"

trap 'rm -f "$TMP"' EXIT


if [ "$1" = "--eol" ]; then
    STRIP_EOL_SPACES="sed -e 's/[ 	]*$//'"
fi

if [ "$2" = "--indent-spaces" ]; then
    # Sigh. `expand --initial` is buggy in coreutils-5.2.1 at least.
    # It ignores tabs after spaces which you can check with:
    # echo -e " \tif" | expand --initial -t4 | grep -qF ' ' && echo buggy
    # It's fixed in coreutils-6.2 at least and probably much earlier,
    # but since the buggy version is in FC4 and ubuntu 5.10
    # we had better work around it by running `unexpand` first.
    TAB_CONVERT="unexpand --first-only -t$3"
    TAB_CONVERT="$TAB_CONVERT | expand --initial -t$3"
elif [ "$2" = "--indent-tabs" ]; then
    TAB_CONVERT="unexpand --first-only -t$3"
fi

[ "$STRIP_EOL_SPACES" ] && COMMAND="$STRIP_EOL_SPACES"
if [ "$TAB_CONVERT" ]; then
    [ "$COMMAND" ] && COMMAND="$COMMAND | "
    COMMAND="$COMMAND$TAB_CONVERT"
fi

[ "$COMMAND" ] || usage

cat -- "$FILE" | eval $COMMAND > "$TMP"
$CMP -s "$TMP" "$FILE" || mv -f "$TMP" "$FILE"
