#!/bin/bash

DICT_PATH=$2
SOURCE_LANG=$3
TARGET_LANG=$4

for i in $(find $1 -type d -exec echo {} \;)
do
  echo "Directory: " $i
  if [ -f ${i}/source.txt ] && [ -f ${i}/target.txt ]; then
    echo "Running hunalign..."
    hunalign -text -utf $DICT_PATH/$SOURCE_LANG-$TARGET_LANG.dic ${i}/source.txt ${i}/target.txt > ${i}/bitext.txt
    echo "Done."
  fi
done

find . -name bitext.txt | xargs cat > $1/joint-corpus.txt
