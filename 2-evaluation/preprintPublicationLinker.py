#!/usr/bin/env python3
# Performs preprint-publication linking by using the Crossref REST API
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
import utils

def printPreprintPublicationMatches(crossref, preprintDoi):
    preprint = crossref.doi(preprintDoi)
    if not preprint:  # Error Crossref e.g.
        print(f'# Unresolvable DOI at Crossref {preprintDoi} thus skipping.')
        return

    preprintTitle = preprint.get('title', [''])[0]
    preprintAuthors = utils.fmtCrossrefAuthors(preprint)
    preprintIssued  = utils.fmtCrossrefDate(preprint['issued'])  # checked on 10.1101/19003376 (issued 9-AUG, created 10-AUG)

    # chop byline because otherwise ‘exceed max line 4096’ (e.g., for 10.1101/2020.09.03.20187252 -> https://tinyurl.com/yxwk9utg)
    res = crossref.query(bibliographic=preprintTitle, author=preprintAuthors[0:2000])\
                  .filter(from_created_date=preprintIssued)\
                  .filter(type='journal-article')\
                  .filter(type='proceedings-article')\
                  .filter(type='book-chapter')\
                  .filter(type='book-part')\
                  .filter(type='book-section')\
                  .select('author,created,DOI,score,title')\
                  .sort('score')\
                  .order('desc')

    print(f"\n\n#--------------------------------------------------------------------------------------------------\n")
    print(f"# Preprint: {preprintDoi}\n# Authors: {preprintAuthors}\n# Title: {preprintTitle}\n# {res.url}")

    resultNbr = 1
    for rank, art in zip(range(1, 20 + 1), res):  # fetching the top20 results only
        publicationDoi = art['DOI'].lower()
        publicationTitle = art.get('title', [''])[0].replace('\n\t', ' ')       # 10.1088/978-1-6432-7034-0ch1 has no title (found via query on 10.1101/268664)
        publicationAuthors = utils.fmtCrossrefAuthors(art)
        publicationIssued  = utils.fmtCrossrefDate(art['created'])    # checked on 10.1016/j.forsciint.2019.109924 & created more reliable than issued (see 10.2106/jbjs.oa.19.00049 where issue is 2020 only)
        score = art['score']

        simTitles = utils.similarity(preprintTitle, publicationTitle)
        matchFound = simTitles >= 0.8 or (simTitles >= 0.1 and (utils.sameFirstAuthorORCID(preprint, art) or utils.sameFirstAuthorNameAndInitial(preprintAuthors, publicationAuthors)))

        print("#" + str(rank))
        if matchFound and not publicationDoi.startswith('10.2139/ssrn'):
            print(f"{preprintDoi}\t{publicationDoi}\t{score}\t{resultNbr}\t{preprintIssued}\t{publicationIssued}\t{publicationTitle}\t{publicationAuthors}")
            resultNbr += 1


def inferPreprintPublicationLinksViaCrossref(dois):
    """Infer a list of doiPublication for each doiPreprint"""
    crossref = cr.Works(etiquette=utils.crossrefEtiquette())
    for doi in dois:
        printPreprintPublicationMatches(crossref, doi)

# Entry point
if __name__ == '__main__':
    inferPreprintPublicationLinksViaCrossref(utils.listDOIs('doi-preprint-list.tsv'))
