#!/usr/bin/env python3
# Shared routines
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

import distance, re
from unidecode import unidecode
from crossref.restful import Etiquette

def crossrefEtiquette():
    """ see https://github.com/fabiobatalha/crossrefapi#support-for-polite-requests-etiquette and https://github.com/CrossRef/rest-api-doc#etiquette"""
    return Etiquette('COVID-19 Preprint Tracker', '1.0', 'https://www.irit.fr/~Guillaume.Cabanac/covid19-preprint-tracker', 'guillaume.cabanac@univ-tlse3.fr')

def cleanse(txt):
    """Remove newlines and tabs from text"""
    return txt.replace('\n', ' ').replace('\t', ' ')

def listDOIs(doiFile):
    """Returns the first column (tab-separated) of all rows that do not start with #"""
    return set([ line.split('\t')[0].strip() for line in open(doiFile).readlines() if not line.startswith('#') and len(line.strip()) > 0 ])

def fmtCrossrefAuthors(json):
    """Format Crossref JSON for authors as lastname, firstnames"""
    if not json.get('author'):  # no authors in 10.3906/sag-2005-82
        return ""
    res = ""        
    for a in json['author']:
        if a.get('family'):
            if a.get('given'):
                res += a.get('family') + ', ' + a.get('given')
            else:
                res += a.get('family')
        else: # 10.1126/science.abb6105 {'name': 'Open COVID-19 Data Working Group†', 'sequence': 'additional', 'affiliation': []}
            if a.get('name'):
                res += a.get('name')
            else:
                res += "No Name Given"
        res += '; '
    return res.rstrip('; ')

def fmtCrossrefDate(json):
    """Format as YYYY-MM-DD the date that is split into 3 chunks"""
    import datetime
    date = json['date-parts'][0]
    y = date[0]
    m = date[1] if len(date) >= 2 else 1 # 2001 -> 2001-01-01 
    d = date[2] if len(date) >= 3 else 1 # 2001-04 -> 2001-04-01
    return datetime.date(y, m, d)  # transforms (2019, 6, 1) -> 2019-06-01 (adding leading zeroes)

def sameFirstAuthorNameAndInitial(byline1, byline2):
    """Checks if the first author from two bylines is likely to be the same person, accounting for accentuated letters and initials in given names"""
    from unidecode import unidecode
    firstAuthor1 = unidecode(byline1.split(';')[0]).replace('-', ' ') # e.g., Ana Fernandez-Cruz ~ Ana Fernández Cruz (10.1101/2020.05.22.20110544)
    firstAuthor2 = unidecode(byline2.split(';')[0]).replace('-', ' ')

    lnfn1 = firstAuthor1.split(',')
    lnfn2 = firstAuthor2.split(',')

    # Comparing last names
    if len(lnfn1) == 1 or len(lnfn2) == 1:                    # no comma found
        return firstAuthor1.lower() == firstAuthor2.lower()
    if lnfn1[0].strip().lower() != lnfn2[0].strip().lower():  # no matching last names
        return False
    
    # Comparing first names
    fn1 = lnfn1[1].strip()
    fn2 = lnfn2[1].strip()
    if fn1 == fn1.upper() or fn2 == fn2.upper():  # Initials only (unless first names recorded in uppercase by Crossref?)
        return fn1[0] == fn2[0]

    lenmin = min(3, len(fn1), len(fn2))
    return fn1[0:lenmin].lower() == fn2[0:lenmin].lower() # match on the 3 first characters?

def sameFirstAuthorORCID(art1, art2):
    """Checks if the ORCIDs of the first author from art1 and art2 match"""
    orcid1 = art1['author'][0].get('ORCID')
    orcid2 = art2['author'][0].get('ORCID')
    return orcid1 != None and orcid2 != None and orcid1 == orcid2

def similarity(txt1, txt2, func=distance.jaccard): # jaccard = best fit for medrxiv data
    """Text similarity on tokenized texts"""
    def asTokens(txt):
        # Uniformise
        txt = unidecode(txt)  # change various hyphens: ‐|-|–           
        # Expand acronyms
        txt = re.sub('\\bSARS[- ]*CoV[- ]*2\\b', 'Severe Acute Respiratory Syndrome Coronavirus', txt, flags=re.IGNORECASE) # SARS‐CoV             ‐2 asym...  (special dash + many spaces)
        txt = re.sub('\\bUSA\\b', 'United States of America', txt)
        txt = re.sub('\\bUS\\b', 'United States', txt)
        txt = txt.lower()
        # Tokenize
        blacklist = ['', 'a', 'an', 'and', 'in', 'of', 'on', 'the', 'to']
        tokens = []
        for token in re.split('[^\\w\\d/-]', txt.lower()): # delimiter is non-word except dash (covid-19, non-randomized, open-label)
            if not token in blacklist:
                if len(token) > 1: # in some titles <p> -- tokenized as --> p
                    tokens.append(token if len(token) <= 2 else token[:-1] if token[-1] == 's' else token) # s-stemmer for words with length 3+
        return tokens
    return 1 - func(asTokens(txt1), asTokens(txt2))

#-- tests -------------------------------------------------------------------------------------------------
def testSameFirstAuthorNameAndInitial():
    print("Should be True:")
    print(sameFirstAuthorNameAndInitial('Rowland, Matthew James; Veenith, Tonny', 'Rowland, Matthew James; Veenith, Tonny'))
    print(sameFirstAuthorNameAndInitial('Rowland, Matthew James; Veenith, Tonny', 'Rowland, M.J.; Veenith, Tonny'))
    print(sameFirstAuthorNameAndInitial('Rowland, Matthew James; Veenith, Tonny', 'Rowland, MJ; Veenith, Tonny'))
    print(sameFirstAuthorNameAndInitial('Rowland, Matthew James; Veenith, Tonny', 'Rowland, M; Veenith, Tonny'))
    print(sameFirstAuthorNameAndInitial('Eponge, Bob; Eastwood, Clint', 'Eponge, B.; Eastwood, C.'))
    print(sameFirstAuthorNameAndInitial('Eponge, Bob; Eastwood, Clint', 'Éponge, B.; Eastwood, C.'))
    print(sameFirstAuthorNameAndInitial('Eponge, Bob; Eastwood, Clint', 'Eponge, Bobby; Eastwood, C.'))
    print(sameFirstAuthorNameAndInitial('Noerz, Dominik; Fischer, Nicole', 'Nörz, Dominik; Fischer, Nicole'))
    print(sameFirstAuthorNameAndInitial('Hosatte-Ducassy, Caroline; Correa, Jose', 'Hosatte‐Ducassy, Caroline; Correa, Jose'))

    print("Should be False:")
    print(sameFirstAuthorNameAndInitial('Rowland, Matthew James; Veenith, Tonny', 'Rowland, Bob; Veenith, Tonny'))
    print(sameFirstAuthorNameAndInitial('Rowland, Matthew James; Veenith, Tonny', 'Rowland, Manuel; Veenith, Tonny'))
    print(sameFirstAuthorNameAndInitial('Rowland, Matthew James; Veenith, Tonny', 'Rowlander, Matthew James; Veenith, Tonny'))
    print(sameFirstAuthorNameAndInitial('Eponge, Bob; Eastwood, Clint', 'Chan, B.; Eastwood, C.'))
    print(sameFirstAuthorNameAndInitial('Eponge, Bob; Eastwood, Clint', 'Eponge, B. Melville, III; Eastwood, C.'))    
    print(sameFirstAuthorNameAndInitial('Eponge, Bob; Eastwood, Clint', 'Eponge, Zorba, III; Eastwood, C.'))
    print(sameFirstAuthorNameAndInitial('Eponge, Bob; Eastwood, Clint', 'Eponge, Barbara; Eastwood, C.'))

def testSameFirstAuthorORCID():
    import crossref.restful as cr
    crossref = cr.Works(etiquette=utils.crossrefEtiquette())
    print("Should be True:")
    print(sameFirstAuthorORCID(crossref.doi('10.1101/19007104'), crossref.doi('10.1371/journal.pone.0232596')))
    print("Should be False:")
    print(sameFirstAuthorORCID(crossref.doi('10.1101/19009456'), crossref.doi('10.1093/annonc/mdz261.007')))
    print(sameFirstAuthorORCID(crossref.doi('10.1101/19012856'), crossref.doi('10.17513/mjpfi.12945')))
    print(sameFirstAuthorORCID(crossref.doi('10.1101/19004994'), crossref.doi('10.1177/2047487319882512')))

# Entry point
if __name__ == '__main__':    
    testSameFirstAuthorNameAndInitial()
    #print(fmtCrossrefDate({'date-parts': [[2010, 6, 30]]} ))