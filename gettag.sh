#!/bin/bash
if [[ ! -e $1 ]] ; then

 echo 'file missing or not specified'

 exit 0

fi

#file="/Users/roarvestre/Dropbox/BearNotes/test/Arang – a Ghost - 2018-02-07_0952.textbundle"
JSON="$(xattr -p com.apple.metadata:_kMDItemUserTags "$1" | xxd -r -p | plutil -convert json - -o -)"

# echo $JSON
echo $JSON > "$2"
#"/Users/roarvestre/GitHub/Bear-Markdown-Export/gettag.txt"
