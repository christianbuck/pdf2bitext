#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
import re
import urlparse
from collections import namedtuple

from languagestripper import LanguageStripper

helptext = """
Take pdf links from stdin and write candidates,
i.e. url with some language identifier removed to stdout.

Input format:
page_url <TAB> pdf_href <TAB> link_text

Example:
http://000sweb.co.monterey.ca.us/assessor/<TAB>\
forms/REQUEST%20FOR%20REVIEW.pdf<TAB>review<TAB\
requests

"""


def read_candidates(infile, valid_hosts=None):
    """ Read candidate urls from previous runs of this script """
    Candidate = namedtuple('Candidate', 'link, page, href, text')
    candidates = {}
    for line in infile:
        try:
            stripped_uri, target_link, target_page, \
                target_href, link_text = line.split("\t")
        except:
            sys.stderr.write("Malformed input: '%s'" % line)
            continue
        candidates[stripped_uri] = Candidate(
            target_link, target_page, target_href, link_text)
    sys.stderr.write("Read %d candidates\n" % (len(candidates)))
    return candidates


def print_match(stripped_url,
                source_url, target_url,
                source_page, target_page):
    print "\t".join([stripped_url,
                     source_url, target_url,
                     source_page, target_page])

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-lang', help='language codes')
    parser.add_argument('-candidates',
                        help='candidates from first pass',
                        type=argparse.FileType('r'))
    args = parser.parse_args(sys.argv[1:])

    language_stripper = LanguageStripper(languages=[args.lang])

    candidates = {}
    if args.candidates:
        candidates = read_candidates(args.candidates)

    for line in sys.stdin:
        line = line.decode('utf-8').split('\t')
        if not len(line) == 3:  # broken line
            continue
        page_url, href, link_text = line
        if not href.lower().endswith('.pdf'):  # broken
            continue

        try:
            joined_link = urlparse.urljoin(page_url, href)
        except ValueError:
            continue

        if candidates and joined_link in candidates:
            target = candidates[joined_link]
            print_match(joined_link,
                        joined_link, target.link,
                        page_url, target.page)
            continue

        parsed_link = urlparse.urlparse(joined_link)

        matched_languages = [language_stripper.match(parsed_link.path),
                             language_stripper.match(parsed_link.query)]

        if args.lang not in matched_languages:
            # we removed a bit of the URL but is does not support our
            # hope to find args.lang, e.g. removed /fr/ when we were looking
            # for Italian pages.
            continue

        stripped_path = language_stripper.strip_path(parsed_link.path)
        stripped_path = re.sub(r'//+', '/', stripped_path)
        stripped_path = re.sub(r'__+', '_', stripped_path)
        stripped_path = re.sub(r'--+', '-', stripped_path)

        stripped_query = language_stripper.strip_query(parsed_link.query)

        netloc = parsed_link.netloc
        if '@' in netloc:
            netloc = netloc.split('@')[1]
        if ':' in netloc:
            netloc = netloc.split(':')[0]
        if not netloc:
            continue

        stripped_uri = urlparse.ParseResult(scheme="http",
                                            netloc=netloc,
                                            path=stripped_path,
                                            params='',
                                            query=stripped_query,
                                            fragment='').geturl()

        # remove new trailing /
        if stripped_uri and stripped_uri[-1] == '/' \
                and parsed_link.path and parsed_link.path[-1] != '/':
            stripped_uri = stripped_uri[:-1]

        if candidates:
            if stripped_uri in candidates:
                target = candidates[stripped_uri]
                print_match(stripped_uri,
                            joined_link, target.link,
                            page_url, target.page)
                continue
        else:
            try:
                sys.stdout.write("\t".join([stripped_uri,
                                            joined_link,
                                            page_url,
                                            href,
                                            link_text]))
                # line still has the newline
            except UnicodeEncodeError:
                pass
