#!/usr/bin/env python3
# Collect all preprint-publication pairs from medrxiv (Gold Standard)
# @author <a href="mailto:guillaume.cabanac@univ-tlse3.fr">Guillaume Cabanac</a>
# @since 02-JUL-2020

# Copyright (C) 2020 Guillaume Cabanac
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import crossref.restful as cr
import requests
import utils

def printPreprintPublicationFromMedrxiv(crossref, doiPreprint):
    """Fetch and print metadata e.g. https://api.biorxiv.org/details/medrxiv/10.1101/2020.02.26.20026971"""
    resp = requests.get(f"https://api.biorxiv.org/details/medrxiv/{doiPreprint}")
    json = resp.json()
    status = json['messages'][0]['status']

    if status != "ok":
        print('# ' + doiPreprint + ' has KO status: ' + status)
        return
    
    # medrxiv
    doiPublication = json['collection'][0]['published'].lower()
    if doiPublication == "na":
        print('# ' + doiPreprint + ' has no associated publication DOI')
        return

    mxPreprintEarliest = json['collection'][0]['date']
    mxPreprintLatest   = json['collection'][-1]['date']
    mxPreprintTitle    = utils.cleanse(json['collection'][-1]['title'])
    mxPreprintAuthors  = json['collection'][-1]['authors']

    # crossref
    crPreprint        = crossref.doi(doiPreprint)
    crPublication     = crossref.doi(doiPublication) # (sometimes NoneType, e.g., 10.34171/mjiri.34.62)

    if not crPreprint or not crPublication:
        print(f"# WARNING: Preprint {doiPreprint} or Publication {doiPublication} not found via Crossref, thus skipping")
        return

    crPreprintTitle   = utils.cleanse(crPreprint['title'][0])
    # checked on 10.1101/19003376 (issued 9-AUG, created 10-AUG)
    crPreprintDate    = utils.fmtCrossrefDate(crPreprint['issued']).isoformat()
    crPreprintAuthors = utils.fmtCrossrefAuthors(crPreprint)
    crPreprintORCID   = crPreprint['author'][0].get('ORCID') or ""
    
    crPublicationTitle   = utils.cleanse(crPublication['title'][0])
    # checked on 10.1016/j.forsciint.2019.109924 & created more reliable than issued (see 10.2106/jbjs.oa.19.00049 where issue is 2020 only)
    crPublicationDate    = utils.fmtCrossrefDate(crPublication['created']).isoformat()
    crPublicationAuthors = utils.fmtCrossrefAuthors(crPublication)
    crPublicationORCID   = crPublication['author'][0].get('ORCID') or ""

    print('\t'.join([doiPreprint, doiPublication, mxPreprintEarliest, mxPreprintLatest, mxPreprintTitle, mxPreprintAuthors,
                                                crPreprintDate, crPreprintTitle, crPreprintAuthors, crPreprintORCID,
                                                crPublicationDate, crPublicationTitle, crPublicationAuthors, crPublicationORCID]))

def extractPreprintPublicationLinksFromMedrxiv(dois):
    """Extract (doiPreprint, doiPublication) from medrxiv and associate metadata from Crossref"""
    crossref = cr.Works(etiquette=utils.crossrefEtiquette())
    for doi in dois:
        printPreprintPublicationFromMedrxiv(crossref, doi)
    print(f"# {len(dois)} pairs in medrxiv gold.")

def rxivPreprintsWithPublications(archive='medrxiv'):
    """Queries *rXiv for preprints-publication links"""
    preprintsWithPublications = set()
    # https://api.biorxiv.org/details/medrxiv/2018-01-01/2020-07-10/10000
    for cursor in range(0, 1000000, 100):  # json["messages"][0]["total"] + 100
        json = requests.get(f"https://api.biorxiv.org/details/{archive}/2000-01-01/3000-01-01/{cursor}").json()  # the entire period of activity
        if json["messages"][0]["status"] != 'ok': break # no more preprints to parse
        for pp in json["collection"]:
            print('\t'.join(["#", pp["doi"].lower(), pp["version"], pp["date"], pp["published"], utils.cleanse(pp["authors"]), utils.cleanse(pp["title"])]))
            if pp["published"] != "NA":
                preprintsWithPublications.add(pp["doi"].lower())
    return preprintsWithPublications

# Entry point
if __name__ == '__main__':
    extractPreprintPublicationLinksFromMedrxiv(rxivPreprintsWithPublications('medrxiv'))