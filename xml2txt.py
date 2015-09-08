#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from StringIO import StringIO
import xml.etree.ElementTree as ET
import subprocess
from external_processor import ExternalProcessor


class TextProcessor(object):

    def __init__(self, splitter=None, tokenizer=None):
        self.split_cmd = splitter
        if tokenizer:
            self.tokenizer = ExternalProcessor(tokenizer)

    def split_sentences(self, text):
        p = subprocess.Popen(self.split_cmd.split(), stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE)
        out, err = p.communicate(input=text.encode("utf-8"))
        return out.decode("utf-8").split("\n")

    def process(self, text):
        if self.split_cmd:
            text = self.split_sentences(text)
        else:
            text = []
        for line in text:
            if self.tokenizer:
                yield self.tokenizer.process(line)
            else:
                yield line


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-lang', help='language', default='en')
    parser.add_argument(
        '-tokenizer', help='call to tokenizer, including arguments')
    parser.add_argument(
        '-splitter', help='call to sentence splitter, including arguments')
    args = parser.parse_args(sys.argv[1:])

    xml = sys.stdin.read()
    parser = ET.XMLParser()
    it = ET.iterparse(StringIO(xml), parser=parser)

    text_processor = TextProcessor(splitter=args.splitter,
                                   tokenizer=args.tokenizer)

    # remove xml namespace, the bane of mankind
    for _, el in it:
        if '}' in el.tag:
            el.tag = el.tag.split('}', 1)[1]  # strip all namespaces
    root = it.root

    for elem in root.findall('head/title/p'):
        print "\n".join(text_processor.process(elem.text))
        print ""

    first = True
    for div in root.findall('body/div'):
        if not first:
            print ""
        first = False
        if div.attrib.get('class', '') == 'page':
            for p in div.findall('p'):
                print "\n".join(text_processor.process(p.text)).encode("utf-8")
