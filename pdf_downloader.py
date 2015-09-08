#!/usr/bin/env python
# -*- coding: utf-8 -*-
from collections import namedtuple
import requests
import sys
import os

""" Download pairs of pdf files 

Input format:
stripped_url<TAB>source_pdf<TAB>target_pdf<TAB>source_page<TAB>target_page
Output:
Directories with a single pair of .pdf file and log file documenting the files'
origins.
"""


def download_pair(candidate, basedir, session):
    source_pdf = candidate.source_url
    target_pdf = candidate.target_url

    # 0. Compute path from hashed url
    h = str(hash(candidate.stripped_url))
    path = os.path.join(basedir, h[1:4], h[4:7], h[7:10])

    if os.path.exists(path):  # slight race condition here
        # Duplicate download?
        return False, "Target path exists already: %s" % path

    # 1. Check that both files exist and are similar size
    try:
        source_r = requests.get(source_pdf, stream=True)
    except requests.exceptions.ConnectionError:
        return False, "connection refused for %s" % source_pdf
    if source_r.status_code != 200:
        return False, "target file not found: %s" % source_pdf
    if 'pdf' not in source_r.headers['content-type']:
        return False, "wrong content type: %s" \
            % source_r.headers['content-type']
    try:
        target_r = requests.get(target_pdf, stream=True)
    except requests.exceptions.ConnectionError:
        return False, "connection refused for %s" % target_pdf
    if target_r.status_code != 200:
        return False, "target file not found: %s" % target_pdf
    if 'pdf' not in target_r.headers['content-type']:
        return False, "wrong content type: %s" \
            % target_r.headers['content-type']

    # 2. Make target directory
    if os.path.exists(path):  # slight race condition here
        # Duplicate download?
        return False, "Target path exists already: %s" % path
    os.makedirs(path)

    # 3. Download pdf and document original names
    l = open(os.path.join(path, "log.txt"), 'wc')
    l.write("%s\t%s\n" % (os.path.join(path, 'source.pdf'), source_pdf))
    l.write("%s\t%s\n" % (os.path.join(path, 'target.pdf'), target_pdf))
    for r, name in [[source_r, 'source.pdf'], [target_r, 'target.pdf']]:
        with open(os.path.join(path, name), 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)
                    f.flush()
    return True, "Success"

CandidatePair = namedtuple('CandidatePair', 'stripped_url, \
                            source_url, target_url, source_page, target_page')


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-lang', help='language codes')
    parser.add_argument('-candidates',
                        help='candidates from url strippper',
                        type=argparse.FileType('r'), default=sys.stdin)
    parser.add_argument('-downloaddir',
                        help='download base directory', required=True)

    args = parser.parse_args(sys.argv[1:])
    assert os.path.exists(args.downloaddir)

    session = requests.Session()
    errors, total = 0, 0
    for line in args.candidates:
        candidate = CandidatePair(*line.split('\t'))
        success, reason = download_pair(candidate, args.downloaddir, session)

        total += 1
        if not success:
            sys.stderr.write("Error %d/%d '%s' processing %s <-> %s\n" %
                             (errors, total, reason,
                              candidate.source_url, candidate.target_url))
            errors += 1

    sys.stderr.write("Wrote %d out of %d candidate pairs\n" %
                     (total - errors, total))
