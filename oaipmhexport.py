from OAIClient import *
from oaipmh import metadata
from oaipmh.datestamp import datestamp_to_datetime
from pymarc.record import *
from MARCXML import MARCXMLReader
import datetime
import properties
import sys
from lxml.etree import XSLT

if len(sys.argv) != 2:
    print "Usage: oaipmhexport.py <mode>"
    exit(1)

oaipmh_host = properties.oaipmh_host
oaipmh_resource = properties.oaipmh_resource
oaipmh_user = properties.user
oaipmh_password = properties.password
oaipmh_metadataprefix = properties.oaipmh_metadataprefix
export_from = properties.export_from
export_to = properties.export_to

fromyear = export_from[0:4]
frommonth = export_from[4:6]
fromday = export_from[6:8]
toyear = export_to[0:4]
tomonth = export_to[4:6]
today = export_to[6:8]
fromdt = datetime.datetime(int(fromyear),int(frommonth),int(fromday),0,0,0,0)
fromds = fromdt.replace(tzinfo=None)
todt = datetime.datetime(int(toyear),int(tomonth),int(today),23,59,59,0)
tods = todt.replace(tzinfo=None)
sigels = properties.sigel_list.split(',')

#mode = deletedbibs
if sys.argv[1] == 'deletedbibs':

    marcxml_reader = MARCXMLReader()
    registry = metadata.MetadataRegistry()
    registry.registerReader(oaipmh_metadataprefix, marcxml_reader)
    oai_hold = Client('http://' + oaipmh_host + oaipmh_resource, registry, credentials=(oaipmh_user,oaipmh_password))

    bibid = None
    all_bibs = set()

    for sigel in sigels:
        bibs = set()

        try:
            for hold_header in oai_hold.listIdentifiers(metadataPrefix=oaipmh_metadataprefix, from_=fromds, until=tods, set='location:%s'%sigel):
                if hold_header.isDeleted():
                    for s in hold_header.setSpec():
                        if s.split(':')[0] == 'bibid':
                            bibs.add(s.split(':')[1])
                            
            #check if bibid has other holds
            bibs2 = set()
            for bibid in bibs:
                if bibid not in all_bibs:
                    for h in oai_hold.listIdentifiers(metadataPrefix=oaipmh_metadataprefix, set='bibid:%s' % bibid):
                        if not h.isDeleted():
                            for s in h.setSpec():
                                if s.split(':')[0] == 'location' and s.split(':')[1] in sigels:
                                    if bibid in bibs:
                                        bibs2.add(bibid)
            bibs.difference_update(bibs2)

        except Exception as e:
            if type(e) == urllib2.HTTPError and e.code == 401:
                print "Unauthorized. Check credentials in properties.py"
            else:
                print "%s : %s" % (type(e), e)
            exit(1)
            
        all_bibs.update(bibs)

    for bibid in sorted(all_bibs, key=int):
        print bibid

#mode = exportrecords
if sys.argv[1] == 'exportrecords':
    
   xml_reader = MARCXMLReader()
   registry = metadata.MetadataRegistry()
   registry.registerReader(oaipmh_metadataprefix, xml_reader)
   oai_client = Client('http://' + oaipmh_host + oaipmh_resource, registry, credentials=(oaipmh_user,oaipmh_password))
   stylesheet = properties.stylesheet

   try:
       for sigel in sigels:
            for record in oai_client.listRecords(metadataPrefix=oaipmh_metadataprefix, from_=fromds, until=tods, set='location:%s'%sigel):
                    record_as_marcxml = record[1]
                    print record_as_marcxml

                    #xslt transform
                    if stylesheet != '':
                        transform = etree.XSLT(etree.XML(open(stylesheet, 'r').read()))
                        result = transform(etree.XML(record_as_marcxml))
                        print result
   except Exception as e:
        if type(e) == urllib2.HTTPError and e.code == 401:
            print "Unauthorized. Check credentials in properties.py"
        else:
            print "%s : %s" % (type(e), e)
        exit(1)




    