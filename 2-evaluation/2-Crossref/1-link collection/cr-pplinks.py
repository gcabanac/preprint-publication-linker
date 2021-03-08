#!/usr/bin/env python3
# Harvest preprint-publication links from Crossref
# @author <a href="mailto:guillaume.cabanac@univ-tlse3.fr">Guillaume Cabanac</a>
# @since 08-JAN-2021

# Copyright (C) 2021 Guillaume Cabanac
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

# Crossref (https://github.com/fabiobatalha/crossrefapi)
import crossref.restful as cr
import jmespath, requests

cr = cr.Works(etiquette=cr.Etiquette('Preprint-Publication Linker', '1.0', 'https://www.irit.fr/~Guillaume.Cabanac', 'guillaume.cabanac@univ-tlse3.fr'))

# e.g., https://api.crossref.org/works?filter=relation.type%3Ais-preprint-of%2Cfrom-pub-date%3A2019-09%2Cuntil-pub-date%3A2019-09&sample=100&select=DOI%2Cpublisher%2Crelation
for year in range(2017, 2020+1):
    for month in range(1, 12+1):
        ym = f'{year}-{month:02d}'
        res = cr.filter(relation__type='is-preprint-of', from_pub_date=ym, until_pub_date=ym).select('DOI,relation,publisher').sample(100)

        for i, preprint in zip(range(1, 100+1), res):
            doiPublisher       = preprint['publisher']
            doiPreprint        = preprint['DOI']
            doiPublication     = preprint['relation']['is-preprint-of'][0]['id']
            doiPublicationRegistrationAgency = jmespath.search('[0].RA', requests.get(f"https://doi.org/doiRA/{doiPublication}").json()) or "Unassigned"

            print(f'{ym}-{i:03d}\t{doiPreprint.lower()}\t{doiPublication.lower()}\t{doiPublisher}\t{doiPublicationRegistrationAgency}')