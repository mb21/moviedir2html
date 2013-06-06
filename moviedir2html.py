#!/usr/bin/env python

import sys, os, re, json, urllib, urllib2, time, codecs, HTMLParser, argparse, traceback
from datetime import date

# wait time in seconds between omdb requests
requestSleepTime = 0.2

# words filtered out in a filename when searching on the internets (case insensitive)
blacklist = ["directorscut", "dts", "aac", "ac3", "uk-release", "release", "screener", "uncut", "cd1", "cd2"]

# if found in a filename, ignore that file
filenameBlacklist = ["CD2", "CD3", "CD4"]

templateDefaultName = os.path.dirname(__file__) + '/movieTemplate.html'

debugMode = False


htmlParser = HTMLParser.HTMLParser()
blacklist = map(lambda x:x.lower(), blacklist)

def toAscii(str):
    return "".join( filter(lambda x: ord(x)<128, str) )


def getMovie(filename):
    "Reads out details from a movie title filename string and returns a dictionary contaning imdb info"
    
    filename = unicode( os.path.basename(filename), 'utf-8')

    # title
    upperCaseTitle = filename
    upperCaseTitle = upperCaseTitle.replace(";", ":")
    title = upperCaseTitle.lower()
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
    upperCaseTitle = upperCaseTitle[:len(title)]
            
    movie = {}
    movie['filename'] = filename
    movie['title'] = title
    movie['year'] = year
    movie['quality'] = quality
    movie['suffix'] = suffix
    movie['comment'] = ""
    movie['upperCaseTitle'] = upperCaseTitle
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
        req = urllib2.Request("http://www.omdbapi.com/?" + query)
        response = urllib2.urlopen(req)
        omdb = json.loads( response.read() )
        response.close()

        if omdb['Response'] == "True" and omdb['Type'] == "movie":
            if len( omdb['tomatoRating'] ) == 1:
                omdb['tomatoRating'] = omdb['tomatoRating'] + ".0"
            omdb['tomatoConsensus'] = htmlParser.unescape(omdb['tomatoConsensus'])
            movie['omdb'] = omdb
            movie['genres'] = map(unicode.strip, omdb['Genre'].split(",") )
            movie['actors'] = map(unicode.strip, omdb['Actors'].split(",") )
            movie['runtime'] = omdb['Runtime'].replace(" h ", ":").replace(" min", "")
            
            # "2:4" -> "2:04"
            shortMatches = re.findall(r':\d$', movie['runtime'])
            if shortMatches:
                movie['runtime'] = movie['runtime'][:-2] + ":0" + movie['runtime'][-1]
            
            # "2 h" -> "2:00"
            shortHourMatches = re.findall(r' h$', movie['runtime'])
            if shortHourMatches:
                movie['runtime'] = movie['runtime'][:-2] + ":00"
                    
            print "found with omdbapi: " + movie['omdb']['Title']

            return movie
        else:
            movie['genres'] = []
            movie['actors'] = []
            return False

    res = askOmdb(movie)
    if not res:
        # search IMDB with Google's i'm feeling lucky
        gquery = 'http://www.google.com/search?q='+urllib.quote_plus( toAscii(movie['title']) + ' film')+'&domains=http%3A%2F%2Fimdb.com&sitesearch=http%3A%2F%2Fimdb.com&btnI=Auf+gut+Gl%C3%BCck%21'
        
        req = urllib2.Request(url=gquery)
        req.add_header('Accept-Language', 'en-US')
        useragent = 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.0.7) Gecko/2009021910 Firefox/3.0.7'
        req.add_header('User-Agent', useragent)
        gr = urllib2.urlopen(req)
        matches = re.findall(r'<title>.*</title>', gr.read())
        gr.close()
        if matches and "site:http://imdb.com" not in matches[0]:
            title = matches[0][7:-15]
            tmatch = re.findall(r' \([a-zA-Z0-9 ]*\)$', title)
            if tmatch:
                title = title.replace(tmatch[0], "")
                movie['year'] = tmatch[0][2:-1]
            print "found on IMDB with Google: " + matches[0] + " -> " + title
            movie['title'] = title
            res = askOmdb(movie)
            if res:
                movie = res
            else:
                movie['genres'] = ["Unknown"]
                movie['title'] = movie['upperCaseTitle']
                print "couldn't find anywhere: '" + title + "', " + movie['year']

    return movie

def checkAndFillIn(movie, movies):
    "if movie not already in movies, add it with fillInFromOmdb"
    filenames = []
    for m in movies:
        filenames.append( m['filename'] )
    
    if not movie['filename'] in filenames:
        movies.append( fillInFromOmdb(movie) )
        time.sleep(requestSleepTime)
    return movies



# MAIN

desc = """Searches directory recursively for movie files and
       writes IMDB information into _movies.html.
       Important: Filenames should be in format: 'US-Title (Year) 720p.mkv',
       where "720" may be any number and "mkv" may also be "mov", "mp4", "avi", or "mpg".
       Notes:
       Empty folders are treated as movie names as well, other
       folders are ignored. Semicolons (;) are treated as colons (:)
       in names. Multipart files should contain 'CD1' or 'CD2',
       only one entry will show up. The tool will only look up movies, no TV series."""

parser = argparse.ArgumentParser(description=desc)
parser.add_argument('--cache', help='generates or uses an existing json cache file. Movies are never removed from the cache, so you can supply the same cache file on different directories to accumulate movies.')
parser.add_argument('--template', help='HTML template file to use (contains the string %%%%%%%%%%json%%%%%%%%%% where the json will be filled in), default is movieTemplate.html in the same directory as this script', default=templateDefaultName)
parser.add_argument('directory', help='the directory to search for movie files')

args = parser.parse_args()

rootdir = args.directory
if not os.path.isdir(rootdir):
    print "Error: please supply a directory"
    sys.exit(0)

if args.cache:
    jsonfile = args.cache
    try:
        # if jsonfile already exists, read in movies
        f = codecs.open(jsonfile, 'r', 'utf-8')
        movies = json.loads( f.read() )
        # remove movies that weren't found on omdb the last time
        movies = filter(lambda m: "omdb" in m, movies)
        f.close()
    except IOError:
        movies = []
else:
    jsonfile = False
    movies = []

def isNotHiddenFile(filename):
    return len( re.findall(r'^\.', os.path.basename(filename)) ) == 0

def filterHiddenFiles(files):
    return filter(isNotHiddenFile, files)

for root, subFolders, files in os.walk(rootdir):
    for filename in filterHiddenFiles(files):
        blacklisted = False
        for word in filenameBlacklist:
            if word in filename:
                blacklisted = True
        if not blacklisted:
            try:
                movie = getMovie(filename)
                if "CD1" in filename:
                    movie['isMultiPartMovie'] = True
                if movie['suffix'] in ["mov", "mp4", "avi", "mkv", "mpg"]:
                    movie['isEmptyDir'] = False
                    movie['path'] = os.path.abspath(os.path.join(root, filename)) 
                    movie['directory'] = os.path.abspath(root) 
                    movies = checkAndFillIn(movie, movies)
            except Exception as e:
                print "Error in: " + filename
                print e
                if debugMode:
                    print traceback.format_exc()

    if len(filterHiddenFiles( os.listdir(root) )) == 0 and isNotHiddenFile(root):
        # empty folder, treat as movie
        try:
            movie = getMovie(root)
            movie['isEmptyDir'] = True
            movie['path'] = os.path.abspath(root) 
            movie['directory'] = os.path.abspath(root) 
            movies = checkAndFillIn(movie, movies)
        except Exception as e:
            print "Error in: " + filename
            print e
            if debugMode:
                print traceback.format_exc()

def titleSortKey(movie):
    if 'omdb' in movie:
        title = movie['omdb']['Title'].lower()
    else:
        title = movie['title'].lower()
    matches = re.findall(r'^(the |a |an )', title)
    if matches:
        title = title.replace(matches[0], "")
    return toAscii(title)

movies.sort(key=titleSortKey)
json = json.dumps(movies)

# write cache file
if jsonfile:
    f = codecs.open(jsonfile, 'w', 'utf-8')
    f.write(json)
    f.close()

# write _movies.html
try:
    tf = codecs.open(args.template, 'r', 'utf-8')
    html = tf.read()

    html = html.replace("%%%%%json%%%%%", json)

    out = codecs.open("_movies.html", 'w', 'utf-8')
    out.write(html)
    out.close()
    tf.close()
except Exception as e:
    print e
    print "Please put the file movieTemplate.html back in the same directory as the script, or supply your own with --template."
