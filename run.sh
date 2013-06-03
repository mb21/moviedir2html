#!/bin/bash

dir="$( dirname "${BASH_SOURCE[0]}" )"
$dir/movies.py . _movies.json
$dir/makeHtml.py $dir/movieTemplate.html _movies.json
