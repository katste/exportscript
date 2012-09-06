#!/usr/bin/env python
"""
Python OAI-PMH MARC Client
Usage: <python deletebib.py YYYYMMDD YYYYMMDD sigel>. First argument=from date, second argument=until date.
"""
from OAIClient import *
from oaipmh import metadata
from oaipmh.datestamp import datestamp_to_datetime
from cStringIO import StringIO
from lxml.etree import tostring, XPathEvaluator
from pymarc.record import *
from MARCXML import MARCXMLReader
import datetime
import sys
import properties


if len(sys.argv) != 4:
    print "Usage: deletebib.py <YYYYMMDD> <YYYYMMDD> <sigel1>[,sigel2,sigel3,...,sigeln]"
    exit(1)

marcxml_reader = MARCXMLReader()
oaipmh_host = 'http://data.libris.kb.se'

from_time = sys.argv[1]
until = sys.argv[2]
sigels = sys.argv[3].split(',')

user = properties.user
password = properties.password

registry = metadata.MetadataRegistry()
registry.registerReader('marcxml', marcxml_reader)

fromyear = from_time[0:4]
frommonth = from_time[4:6]
fromday = from_time[6:8]
toyear = until[0:4]
tomonth = until[4:6]
today = until[6:8]

oai_bib = Client(oaipmh_host + '/bib/oaipmh', registry, credentials=(user,password))
oai_hold = Client(oaipmh_host + '/hold/oaipmh', registry, credentials=(user,password))

fromdt = datetime.datetime(int(fromyear),int(frommonth),int(fromday),0,0,0,0)
fromds = fromdt.replace(tzinfo=None)

todt = datetime.datetime(int(toyear),int(tomonth),int(today),23,59,59,0)
tods = todt.replace(tzinfo=None)
bibid = None
all_bibs = set()

for sigel in sigels:
    bibs = set()

    try:
        for hold_header in oai_hold.listIdentifiers(metadataPrefix='marcxml', from_=fromds, until=tods, set='location:%s'%sigel):
            if hold_header.isDeleted():
                for s in hold_header.setSpec():
                    if s.split(':')[0] == 'bibid':
                        bibs.add(s.split(':')[1])

        #check if bibid has other holds
        bibs2 = set()
        for bibid in bibs:
            if bibid not in all_bibs:
                for h in oai_hold.listIdentifiers(metadataPrefix='marcxml', set='bibid:%s' % bibid):
                    if not h.isDeleted():
                        for s in h.setSpec():
                            if s.split(':')[0] == 'location' and s.split(':')[1] in sigels:
                                if bibid in bibs:
                                    bibs2.add(bibid)

        bibs.difference_update(bibs2)

    except urllib2.HTTPError, e:
        if e.code == 401:
            print "Unauthorized. Check credentials in properties.py"
            exit(1)

    all_bibs.update(bibs)

for bibid in sorted(all_bibs, key=int):
    print bibid

