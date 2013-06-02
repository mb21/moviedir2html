#!/usr/bin/env python

import sys, os, re, json, urllib, requests, time
from datetime import date

# words ignored in a filename when searching on the internets
blacklist = map(lambda x:x.lower(), ["directorscut", "dts", "aac", "ac3", "uk-release", "release", "screener", "uncut"] )


def getMovie(filename):
    "Reads out details from a movie title filename string and returns a dictionary"
    filename = os.path.basename(filename)
    title = filename.lower()
    
    # title
    for word in blacklist:
        title = title.replace(word, "")

    # year
    yearMatches = re.findall(r'\(\d{4}\)', title) # find "(1990)"
    if yearMatches:
        yearint = int( yearMatches[0][1:-1] )
        if yearint > 1920 and yearint <= date.today().year:
            year = str(yearint)
            title = title.replace(yearMatches[0], "")
    else:
        year = ""

    # quality
    qualityMatches = re.findall(r' ((\d)?\d{3})p', title)
    if qualityMatches:
        quality = qualityMatches[0][0].strip() + "p"
    elif title.find("dvdrip") > 0:
        quality = "DVDRip"
    else:
        quality = ""
    title = title.replace(quality.lower(), "")

    # suffix
    suffixMatches = re.findall(r'\.\w{3}$', title)
    if suffixMatches:
        suffix = suffixMatches[0]
        title = title.replace(suffix, "")
        suffix = suffix.replace(".", "")
        suffix = suffix.lower()
    else:
        suffix = ""

    title = title.strip()
    
    movie = {}
    movie['filename'] = filename
    movie['title'] = title
    movie['year'] = year
    movie['quality'] = quality
    movie['suffix'] = suffix
    movie['comment'] = ""
    return movie


def fillInFromOmdb(movie):
    "fills in data from www.omdbapi.com"
    parameters = [
        ("t", movie['title']),
        ("y", movie['year']),
        ("tomatoes", "true"),
        ("plot", "full")
    ]
    query = urllib.urlencode(parameters, True)
    r = requests.get("http://www.omdbapi.com/?" + query)
    omdb = json.loads(r.content)
    if omdb['Response'] == "True":
        movie['omdb'] = omdb
        print "filled in " + movie['omdb']['Title']
    else:
        print "couldn't find " + movie['title']
        # TODO: Google it with https://developers.google.com/custom-search/v1/overview
        # Google API limit: 100 queries per day

    return movie


def checkAndFillIn(movie, movies):
    filenames = []
    for m in movies:
        filenames.append( m['filename'] )
    if not movie['filename'] in filenames:
        movies.append( fillInFromOmdb(movie) )
        time.sleep(1)
    return movies


# MAIN

if len(sys.argv) <= 2:
    print "usage: movies.py directory file.json"
    print "       Searches directory for movie files and prints into file.json"
    sys.exit(0)

rootdir = sys.argv[1]
if not os.path.isdir(rootdir):
    print "Error: first argument must be a directory"
    sys.exit(0)

jsonfile = sys.argv[2]

try:
    f = open(jsonfile, 'r')
    movies = json.loads( f.read() )
    f.close()
except IOError:
    movies = []

f = open(jsonfile, 'w')

for root, subFolders, files in os.walk(rootdir):

    for filename in files:
        movie = getMovie(filename)
        if movie['suffix'] in ["mov", "mp4", "avi", "mkv", "mpg"]:
            movie['isEmptyDir'] = False
            movie['path'] = os.path.abspath(os.path.join(root, filename)) 
            movie['directory'] = os.path.abspath(root) 
            movies = checkAndFillIn(movie, movies)

    if not os.listdir(root):
        # empty folder, treat as movie
        movie = getMovie(root)
        movie['isEmptyDir'] = True
        movie['path'] = os.path.abspath(root) 
        movie['directory'] = os.path.abspath(root) 
        movies = checkAndFillIn(movie, movies)

f.write( json.dumps(movies) )
f.close()
