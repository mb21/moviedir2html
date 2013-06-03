#!/usr/bin/env python

import sys

if len(sys.argv) <= 2:
    print "usage: makeHtml.py template.html movies.json"
    sys.exit(0)

templatefile = sys.argv[1]
jsonfile = sys.argv[2]

tf = open(templatefile, 'r')
jf = open(jsonfile, 'r')

html = tf.read()
json = jf.read()

html = html.replace("%%%%%json%%%%%", json)

out = open("_movies.html", 'w')
out.write(html)

tf.close()
jf.close()
out.close()
