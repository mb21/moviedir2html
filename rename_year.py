#!/usr/bin/env python

# "Harry 1999 720p" -> "Harry (1999) 720p"
# Recursively on directory

import sys, os, re
from datetime import date

if len(sys.argv) <= 1:
    print "'Harry 1999 720p' -> 'Harry (1999) 720p'. Usage: give the directory as an argument."
    sys.exit(0)

rootdir = sys.argv[1]

for root, subFolders, files in os.walk(rootdir):
    for filename in files + subFolders:
        matches = re.findall(r' \d{4}', filename)
        if matches:
            year = int( matches[0].strip() )
            if year > 1920 and year <= date.today().year:
                yearstr = str(year)
                newfilename = filename.replace(yearstr, "("+yearstr+")")
                if filename != newfilename:
                    os.rename( os.path.join(root, filename), os.path.join(root, newfilename) )
                    print "Renamed to", newfilename
