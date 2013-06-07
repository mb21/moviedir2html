# moviedir2html.py

Searches a directory recursively for movie files and writes IMDB information into a HTML file.

**Important:** Filenames should be in format: "Title (Year) 720p.mkv", where "720" may be any number and "mkv" may also be "mov", "mp4", "avi", or "mpg".

The HTML is generated from the movieTemplate.html file which you can modify. The default contains a simplistic and beautiful GUI (rendered with AngularJS) to browse all movies and filter by categories and fulltext search.

Notes:

* Empty folders are treated as movie names as well, other folders are ignored.
* Semicolons (;) are treated as colons (:) in names.
* Multipart files should contain 'CD1' or 'CD2', only one entry will show up.
* The tool will only look up movies, no TV series.
* Requires Python 2.7.x

## Screenshot of output
![Screenshot](https://raw.github.com/mb21/moviedir2html/master/screenshot.jpg)

## Usage

```
python moviedir2html.py [-h] [--cache CACHE] [--template TEMPLATE] directory

positional arguments:
  directory            the directory to search for movie files

optional arguments:
  -h, --help           show this help message and exit
  --cache CACHE        generates or uses an existing json cache file. Movies
                       are never removed from the cache, so you can supply the
                       same cache file on different directories to accumulate
                       movies.
  --template TEMPLATE  HTML template file to use (contains the string
                       %%%%%json%%%%% where the json will be filled in),
                       default is movieTemplate.html in the same directory as
                       this script
```
