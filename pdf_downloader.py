#!/usr/bin/env python
# -*- coding: utf-8 -*-
from collections import namedtuple
from itertools import imap
import multiprocessing
import os
import requests
import shutil
import sys

""" Download pairs of pdf files

Input format:
stripped_url<TAB>source_pdf<TAB>target_pdf<TAB>source_page<TAB>target_page
Output:
Directories with a single pair of .pdf file and log file documenting the files'
origins.
"""


def make_request(url):
    try:
        r = requests.get(url, stream=True)
    except requests.exceptions.ConnectionError:
        return False, "connection refused for %s" % url
    except requests.exceptions.InvalidSchema:
        return False, "invalid schema %s" % url
    except requests.exceptions.TooManyRedirects:
        return False, "too many redirects for %s" % url
    except (KeyboardInterrupt, SystemExit):
        raise
    except Exception as e:
        return False, "other error: %s" % str(e)
    if r.status_code != 200:
        return False, "file not found: %s" % url
    if 'pdf' not in r.headers.get('content-type', '').lower():
        return False, "wrong content type: %s" \
            % r.headers['content-type']
    return True, r


def download_pair(candidate, basedir, session):
    source_pdf = candidate.source_url
    target_pdf = candidate.target_url

    # 0. Compute path from hashed url
    h = str(hash(candidate.stripped_url))
    path = os.path.join(basedir, h[1:4], h[4:7], h[7:10])

    if os.path.exists(path):  # slight race condition here
        # Duplicate download?
        return False, "Target path exists already: %s" % path

    # 1. Check that both files exist and have correct type
    success, source_r = make_request(source_pdf)
    if not success:
        reason = source_r
        return False, reason

    success, target_r = make_request(target_pdf)
    if not success:
        reason = target_r
        return False, reason

    # 2. Make target directory
    if os.path.exists(path):  # slight race condition here
        # Duplicate download?
        return False, "Target path exists already: %s" % path

    try: 
        os.makedirs(path)
    except OSError:
        return False, "Target path exists already: %s" % path

    # 3. Download pdf and document original names
    l = open(os.path.join(path, "log.txt"), 'wc')
    l.write("%s\t%s\n" % (os.path.join(path, 'source.pdf'), source_pdf))
    l.write("%s\t%s\n" % (os.path.join(path, 'target.pdf'), target_pdf))
    try:
        for r, name in [[source_r, 'source.pdf'], [target_r, 'target.pdf']]:
            with open(os.path.join(path, name), 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
    except (KeyboardInterrupt, SystemExit):
        raise
    except:
        shutil.rmtree(path, ignore_errors=True)
        return False, "download error"
    return True, "Success"

CandidatePair = namedtuple('CandidatePair', 'stripped_url, \
                            source_url, target_url, source_page, target_page')

session = requests.Session()


def process_line(line):
    candidate = CandidatePair(*line.split('\t'))
    success, reason = download_pair(candidate, args.downloaddir, session)
    return success, reason, candidate


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-lang', help='language codes')
    parser.add_argument('-candidates',
                        help='candidates from url strippper',
                        type=argparse.FileType('r'), default=sys.stdin)
    parser.add_argument('-downloaddir',
                        help='download base directory', required=True)
    parser.add_argument('-threads', default=1, type=int,
                        help='Number of concurrent downloads')

    args = parser.parse_args(sys.argv[1:])
    assert os.path.exists(args.downloaddir)

    errors, total = 0, 0

    it = None
    if args.threads > 1:
        pool = multiprocessing.Pool(processes=args.threads)
        it = pool.imap_unordered(process_line, args.candidates)
    else:
        it = imap(process_line, args.candidates)

    for success, reason, candidate in it:
        total += 1
        if not success:
            sys.stderr.write("Error %d/%d '%s' processing %s <-> %s\n" %
                             (errors, total, reason,
                              candidate.source_url, candidate.target_url))
            errors += 1

    sys.stderr.write("Wrote %d out of %d candidate pairs\n" %
                     (total - errors, total))
