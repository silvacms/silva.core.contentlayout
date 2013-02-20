#/usr/bin/env bash

CLEANCSS=`which cleancss`
if test "$?" != "0" ; then
    echo "clean-css is not installed. Install with npm:"
    echo "npm install -g clean-css"
    exit 1
fi
UGLIFYJS=`which uglifyjs`
if test "$?" != "0" ; then
    echo "uglify-js is not installed. Install with npm:"
    echo "npm install -g uglify-js"
    exit 1
fi

for file in $(find . -name '*.js' -regex '.*/static/.*' |
              grep -ve '\.min\.js$'); do
    echo "Compressing $file ..."
    $UGLIFYJS -nc -o $(echo $file | sed 's/\.js$/.min.js/') $file;
done
for file in $(find . -name '*.css' -not -regex '.*/jqueryui/.*' |
              grep -ve '\.min\.css$'); do
    echo "Compressing $file ..."
    $CLEANCSS -nc -o $(echo $file | sed 's/\.css$/.min.css/') $file;
done
