#!/bin/bash

set -e
set -o pipefail

PDF2XML=/home/buck/net/build/pdf2xml/pdf2xml
XML2TXT='/home/buck/net/build/pdf2bitext/xml2txt.py'
ALIGN=/home/buck/net/build/pdf2bitext/align_with_hunalign.sh

$PDF2XML -T $1/source.pdf > ${1}/source.xml &
$PDF2XML -T $1/target.pdf > ${1}/target.xml &
wait
cat ${1}/source.xml | $XML2TXT -splitter="/home/buck/net/build/mosesdecoder/scripts/ems/support/split-sentences.perl -l en -b -q" -tokenizer="/home/buck/net/build/mosesdecoder/scripts/tokenizer/tokenizer.perl -l en -q -b" > ${1}/source.txt &
cat ${1}/target.xml | $XML2TXT -splitter="/home/buck/net/build/mosesdecoder/scripts/ems/support/split-sentences.perl -l fr -b -q" -tokenizer="/home/buck/net/build/mosesdecoder/scripts/tokenizer/tokenizer.perl -l fr -q -b" > ${1}/target.txt &
wait

$ALIGN -d /home/jorge/dictionaries-hunalign/en-fr.dic $1 2> $1/align.log
grep "^Quality" $1/align.log
wc $1/bitext.txt 

touch ${1}/done        
