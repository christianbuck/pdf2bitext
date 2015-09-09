#!/bin/bash

ERROR=/dev/stderr
DICT_PATH=/dev/null
DIRECTORY=
SOURCE_LANG=en
TARGET_LANG=fr
OUTPUT=

function help()
{
  echo "\
Usage: $1 [options] directory [output]
  Mandatory parameters:
    directory              directory to find and align bitexts with hunalign
  Optional parameters:
    output                 All concatenated files from hunalign outputs joined in one file 
  Options:
    -s, --s_code           source language code of the bitext, default is $s_code
    -t, --t_code           target language code of the bitext, default is $t_code
    -d, --dictionary       path to the dictionary file for hunalign (default /dev/null)
    -h, --help             shows this help" > "$ERROR"
}

# Parse params
if ! options=$(getopt -u -o "s:t:d:h" -l "s_code:,t_code:,dictionary:,help" -- "$@")
then
  help $(basename $0)
  exit 2
fi
  
set -- $options

while [ $# -gt 0 ]
do
  case $1 in
    -s|--s_code)
      s_code="${2}"
      shift
      ;;   
    -t|--t_code)
      t_code="${2}"
      shift
      ;;   
    -d|--dictionary)
      logging="1"
      DICT_PATH="${2}" 
      shift
      ;;   
    -h|--help)
      help $(basename $0)
      exit 0
      ;;
    --) 
      shift
      break
      ;;
    *)     
      help $(basename $0)
      exit 2
      break 
      ;;    
  esac      
  shift     
done        

if [ $# -gt 2 ]; then help $(basename $0); exit 2; fi
if [ $# -ge 1 ]; then DIRECTORY=$1; fi
if [ $# -eq 2 ]; then OUTPUT=$2; fi

if [ $(which hunalign|/usr/bin/wc -l) -eq 0 ]; then
  echo "Error: the tool 'hunalign' could not be found and it is necessary to align the files"
  exit
fi

for i in $(find $DIRECTORY -type d -exec echo {} \;)
do
  echo "Directory: " $i
  if [ -f ${i}/source.txt ] && [ -f ${i}/target.txt ]; then
    echo "Running hunalign..."
    hunalign -text -utf $DICT_PATH ${i}/source.txt ${i}/target.txt > ${i}/bitext.txt
    echo "Done."
  fi
done

if [ "$OUTPUT" != "" ]; then
  find . -name bitext.txt | xargs cat > $OUTPUT
fi
