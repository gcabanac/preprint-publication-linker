#!/usr/bin/env python3
# Analyse medarxiv to find relevant features
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

import re
from datetime import date
import utils

# Entry point
if __name__ == '__main__':
    for gold in list(map(lambda l : re.split('[\t\n]', l), filter(lambda l : not l.startswith('#') and len(l.strip()), open('medrxiv-gold.tsv').readlines()))): 
        preDOI     = gold[0]
        preDate    = gold[6]
        preTitle   = gold[7]
        preAuthors = gold[8]
        preNbAut   = len(gold[8].split(';'))
        preORCID   = gold[9]
        pubDOI     = gold[1]                
        pubDate    = gold[10]
        pubTitle   = gold[11]
        pubAuthors = gold[12]
        pubNbAut   = len(gold[12].split(';'))
        pubORCID   = gold[13]

        matchDate        = date.fromisoformat(preDate) <= date.fromisoformat(pubDate)
        matchFirstAuthor = utils.sameFirstAuthorNameAndInitial(preAuthors, pubAuthors)
        matchORCID       = preORCID == pubORCID if preORCID != '' and pubORCID != '' else False
        matchNbAut       = preNbAut <= pubNbAut
        simTitles        = utils.similarity(preTitle, pubTitle)

        print('\t'.join([preDOI, pubDOI, str(preNbAut), str(pubNbAut), str(matchDate), str(matchFirstAuthor), str(matchORCID), str(matchNbAut), str(simTitles), preTitle, pubTitle]))