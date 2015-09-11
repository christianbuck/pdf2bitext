#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from StringIO import StringIO
import xml.etree.ElementTree as ET
import subprocess
from external_processor import ExternalProcessor

import langid
import chardet


class TextProcessor(object):

    def __init__(self, splitter=None, tokenizer=None):
        self.split_cmd = splitter
        self.tokenizer = None
        if tokenizer:
            self.tokenizer = ExternalProcessor(tokenizer)

    def split_sentences(self, text):
        if not text:
            return []
        p = subprocess.Popen(self.split_cmd.split(), stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE)
        out, err = p.communicate(input=text.encode("utf-8") + "\n")
        return out.decode("utf-8").split("\n")

    def process(self, text):
        if text:
            if self.split_cmd:
                text = self.split_sentences(text)
            else:
                text = [text]
            for line in text:
                if not line.strip():
                    continue
                if self.tokenizer:
                    yield self.tokenizer.process(line).strip()
                else:
                    yield line.strip()


def print_text(root):
    for elem in root.findall('head/title/p'):
        print "\n".join(text_processor.process(elem.text)).encode("utf-8")
        print ""

    first = True
    for div in root.findall('body/div'):
        if not first:
            print ""
        first = False
        if div.attrib.get('class', '') == 'page':
            for p in div.findall('p'):
                print "\n".join(text_processor.process(p.text)).encode("utf-8")


def print_ep(root):
    chapter = 1
    print "<CHAPTER ID=%d>" % chapter
    for elem in root.findall('head/title/p'):
        if not elem.text:
            continue
        print "\n".join(text_processor.process(elem.text))

    page = 1
    for div in root.findall('body/div'):
        if div.attrib.get('class', '') == 'page':
            print "<SPEAKER ID=%d NAME=\"JohnDoe\">" % page
            page += 1
            first = True
            for p in div.findall('p'):
                if not p.text:
                    continue
                if not first:
                    print "<P>"
                first = False
                print "\n".join(text_processor.process(p.text)).encode("utf-8")


def fix_encoding(expected_langs, text, data):
    detected_lang, _confidence = langid.classify(text)
    if detected_lang not in expected_langs:
        enc = chardet.detect(text.encode('raw_unicode_escape'))
        sys.stderr.write(str(enc))
        if enc['encoding'] != 'ascii':
            fixed_text = text.encode(
                'raw_unicode_escape').decode(enc['encoding'])
            detected_lang, _confidence = langid.classify(fixed_text)
            if detected_lang in expected_langs:
                fixed_data = data.decode(
                    'utf-8').encode('raw_unicode_escape').decode(
                    enc['encoding']).encode('utf-8')
                return fixed_data
    return data


def fix_xml_encoding(expected_langs, xml):
    parser = ET.XMLParser()
    it = ET.iterparse(StringIO(xml), parser=parser)
    text = []
    for _, el in it:
        if el.text and el.text.strip():
            text.append(el.text)
    fixed_xml = fix_encoding(expected_langs, "\n".join(text), xml)
    return fixed_xml


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-lang', nargs='+', help='language', default='en')
    parser.add_argument('-ep', help='europarl stye', action='store_true')
    parser.add_argument(
        '-tokenizer', help='call to tokenizer, including arguments')
    parser.add_argument(
        '-splitter', help='call to sentence splitter, including arguments')
    args = parser.parse_args(sys.argv[1:])

    xml = sys.stdin.read()
    xml = fix_xml_encoding(args.lang, xml)
    parser = ET.XMLParser()
    it = ET.iterparse(StringIO(xml), parser=parser)

    text_processor = TextProcessor(splitter=args.splitter,
                                   tokenizer=args.tokenizer)

    # remove xml namespace, the bane of humanity
    for _, el in it:
        if '}' in el.tag:
            el.tag = el.tag.split('}', 1)[1]  # strip all namespaces
    root = it.root

    if args.ep:
        print_ep(root)
    else:
        print_text(root)
