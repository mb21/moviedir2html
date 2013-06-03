#!/usr/bin/env python

import sys, os, re, json, urllib, requests, time, HTMLParser
from datetime import date

# words ignored in a filename when searching on the internets
blacklist = map(lambda x:x.lower(), ["directorscut", "dts", "aac", "ac3", "uk-release", "release", "screener", "uncut", "cd1", "cd2"] )

h = HTMLParser.HTMLParser()

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

    def askOmdb(movie):
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
            if len( omdb['tomatoRating'] ) == 1:
                omdb['tomatoRating'] = omdb['tomatoRating'] + ".0"
            if len( omdb['tomatoConsensus'] ) == 1:
                omdb['tomatoConsensus'] = h.unescape(omdb['tomatoConsensus'])
            movie['omdb'] = omdb
            movie['genres'] = omdb['Genre'].split(",")
            movie['actors'] = omdb['Actors'].split(",")
            movie['runtime'] = omdb['Runtime'].replace(" h ", ":").replace(" min", "")
            print "filled in " + movie['omdb']['Title']

            return movie
        else:
            return {}

    res = askOmdb(movie)
    if res:
        movie = res
    else:
        gquery = 'http://www.google.com/search?q='+urllib.quote_plus(movie['title'])+' film'+'&domains=http%3A%2F%2Fen.wikipedia.org&sitesearch=http%3A%2F%2Fen.wikipedia.org&btnI=Auf+gut+Gl%C3%BCck%21'
        gr = requests.get(gquery)
        #TODO: check if redirected to wikipedia or stayed at google
        matches = re.findall(r'<title>.*</title>', gr.content)
        if matches:
            title = matches[0][7:-43]
            tmatch = re.findall(r' \([a-zA-Z0-9 ]*\)$', title)
            if tmatch:
                title = title.replace(tmatch[0], "")
            print "found on wiki: " + matches[0] + " -> " + title
            movie['title'] = title
            res = askOmdb(movie)
            if res:
                movie = res
            else:
                movie['genres'] = ["Unknown"]
                print "couldn't find " + movie['title']

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

def getTitle(movie):
    if 'omdb' in movie:
        title = "".join( filter( lambda x: ord(x)<128, movie['omdb']['Title'] ))
        return title
    else:
        title = "".join( filter( lambda x: ord(x)<128, movie['title'] ))
        return title

movies.sort(key=getTitle) 

f.write( json.dumps(movies) )
f.close()

