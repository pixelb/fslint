#!/usr/bin/env python
# This is called by findup automatically don't call explicitly
# unless you really know what you're doing.
#
# It expects lines in the format:
# filename1
# filename2
#
# filename3
# filename4
# ...

import sys, string, os

link=1
dryRun=0
if len(sys.argv) == 2:
    if sys.argv[1] == "del":
        link=0
    elif sys.argv[1] == "tdel":
        link=0
        dryRun=1
    elif sys.argv[1] == "tmerge":
        dryRun=1

ingroup = 0
for line in sys.stdin.xreadlines():
    line = string.strip(line)
    if line == '':
        ingroup = 0
    else:
        if not ingroup:
            keep = line
            ingroup = 1
            if dryRun:
                print "\nkeeping", keep + "\t",
                if link:
                    print "hardlinking:",
                else:
                    print "deleting:",
        else:
            if dryRun:
                print line,
            else:
                try:
                    os.unlink(line)
                    if link:
                        os.link(keep,line) #TODO: if error try symlink
                except OSError:
                    sys.stderr.write(str(sys.exc_value)+'\n')
