{\rtf1\ansi\ansicpg1252\cocoartf1138\cocoasubrtf470
{\fonttbl\f0\fmodern\fcharset0 Courier;}
{\colortbl;\red255\green255\blue255;}
\paperw11900\paperh16840\margl1440\margr1440\vieww19560\viewh26000\viewkind0
\deftab720
\pard\pardeftab720

\f0\fs24 \cf0 # Copyright 2003, 2004, 2005 Infrae\
# Released under the BSD license (see LICENSE.txt)\
from __future__ import nested_scopes\
import urllib2\
import base64\
from urllib import urlencode\
from StringIO import StringIO\
from types import SliceType\
from lxml import etree\
import time\
\
from oaipmh import common, metadata, validation, error\
from oaipmh.datestamp import datestamp_to_datetime, datetime_to_datestamp\
\
WAIT_DEFAULT = 120 # two minutes\
WAIT_MAX = 5\
\
class Error(Exception):\
\'a0\'a0\'a0\'a0pass\
\
class LibrisOAIClient(common.OAIPMH):\
\
\'a0\'a0\'a0\'a0def __init__(self, metadata_registry=None):\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0self._metadata_registry = (\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0metadata_registry or metadata.global_metadata_registry)\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0self._ignore_bad_character_hack = 0\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0self._day_granularity = False\
\
\'a0\'a0\'a0\'a0def updateGranularity(self):\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0"""Update the granularity setting dependent on that the server says.\
        """\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0identify = self.identify()\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0granularity = identify.granularity()\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0if granularity == 'YYYY-MM-DD':\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0self._day_granularity = True\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0elif granularity == 'YYYY-MM-DDThh:mm:ssZ':\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0self._day_granularity= False\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0else:\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0raise Error, "Non-standard granularity on server: %s" % granularity\
\
\'a0\'a0\'a0\'a0def handleVerb(self, verb, kw):\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0# validate kw first\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0validation.validateArguments(verb, kw)\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0# encode datetimes as datestamps\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0from_ = kw.get('from_')\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0if from_ is not None:\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0# turn it into 'from', not 'from_' before doing actual request\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0kw['from'] = datetime_to_datestamp(from_,\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0self._day_granularity)\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0if 'from_' in kw:\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0# always remove it from the kw, no matter whether it be None or not\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0del kw['from_']\
\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0until = kw.get('until')\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0if until is not None:\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0kw['until'] = datetime_to_datestamp(until,\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0self._day_granularity)\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0elif 'until' in kw:\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0# until is None but is explicitly in kw, remove it\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0del kw['until']\
\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0# now call underlying implementation\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0method_name = verb + '_impl'\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0return getattr(self, method_name)(\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0kw, self.makeRequestErrorHandling(verb=verb, **kw))\
\
\'a0\'a0\'a0\'a0def getNamespaces(self):\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0"""Get OAI namespaces.\
        """\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0return \{'oai': 'http://www.openarchives.org/OAI/2.0/'\}\
\
\'a0\'a0\'a0\'a0def getMetadataRegistry(self):\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0"""Return the metadata registry in use.\
\
        Do we want to allow the returning of the global registry?\
        """\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0return self._metadata_registry\
\
\'a0\'a0\'a0\'a0def ignoreBadCharacters(self, true_or_false):\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0"""Set to ignore bad characters in UTF-8 input.\
        This is a hack to get around well-formedness errors of\
        input sources which *should* be in UTF-8 but for some reason\
        aren't completely.\
        """\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0self._ignore_bad_character_hack = true_or_false\
\
\'a0\'a0\'a0\'a0def parse(self, xml):\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0"""Parse the XML to a lxml tree.\
        """\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0# XXX this is only safe for UTF-8 encoded content,\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0# and we're basically hacking around non-wellformedness anyway,\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0# but oh well\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0if self._ignore_bad_character_hack:\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0xml = unicode(xml, 'UTF-8', 'replace')\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0# also get rid of character code 12\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0xml = xml.replace(chr(12), '?')\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0xml = xml.encode('UTF-8')\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0return etree.XML(xml)\
\
\'a0\'a0\'a0\'a0def GetRecord_impl(self, args, tree):\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0records, token = self.buildRecords(\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0args['metadataPrefix'],\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0self.getNamespaces(),\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0self._metadata_registry,\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0tree\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0)\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0assert token is None\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0return records[0]\
\
\'a0\'a0\'a0\'a0# implementation of the various methods, delegated here by\
\'a0\'a0\'a0\'a0# handleVerb method\
\
\'a0\'a0\'a0\'a0def Identify_impl(self, args, tree):\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0namespaces = self.getNamespaces()\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0evaluator = etree.XPathEvaluator(tree, namespaces=namespaces)\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0identify_node = evaluator.evaluate(\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0'/oai:OAI-PMH/oai:Identify')[0]\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0identify_evaluator = etree.XPathEvaluator(identify_node,\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0namespaces=namespaces)\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0e = identify_evaluator.evaluate\
\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0repositoryName = e('string(oai:repositoryName/text())')\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0baseURL = e('string(oai:baseURL/text())')\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0protocolVersion = e('string(oai:protocolVersion/text())')\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0adminEmails = e('oai:adminEmail/text()')\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0earliestDatestamp = datestamp_to_datetime(\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0e('string(oai:earliestDatestamp/text())'))\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0deletedRecord = e('string(oai:deletedRecord/text())')\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0granularity = e('string(oai:granularity/text())')\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0compression = e('oai:compression/text()')\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0# XXX description\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0identify = common.Identify(\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0repositoryName, baseURL, protocolVersion,\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0adminEmails, earliestDatestamp,\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0deletedRecord, granularity, compression)\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0return identify\
\
\'a0\'a0\'a0\'a0def ListIdentifiers_impl(self, args, tree):\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0namespaces = self.getNamespaces()\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0def firstBatch():\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0return self.buildIdentifiers(namespaces, tree)\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0def nextBatch(token):\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0tree = self.makeRequestErrorHandling(verb='ListIdentifiers',\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0resumptionToken=token)\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0return self.buildIdentifiers(namespaces, tree)\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0return ResumptionListGenerator(firstBatch, nextBatch)\
\
\'a0\'a0\'a0\'a0def ListMetadataFormats_impl(self, args, tree):\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0namespaces = self.getNamespaces()\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0evaluator = etree.XPathEvaluator(tree,\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0namespaces=namespaces)\
\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0metadataFormat_nodes = evaluator.evaluate(\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0'/oai:OAI-PMH/oai:ListMetadataFormats/oai:metadataFormat')\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0metadataFormats = []\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0for metadataFormat_node in metadataFormat_nodes:\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0e = etree.XPathEvaluator(metadataFormat_node,\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0namespaces=namespaces).evaluate\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0metadataPrefix = e('string(oai:metadataPrefix/text())')\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0schema = e('string(oai:schema/text())')\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0metadataNamespace = e('string(oai:metadataNamespace/text())')\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0metadataFormat = (metadataPrefix, schema, metadataNamespace)\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0metadataFormats.append(metadataFormat)\
\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0return metadataFormats\
\
\'a0\'a0\'a0\'a0def ListRecords_impl(self, args, tree):\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0namespaces = self.getNamespaces()\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0metadata_prefix = args['metadataPrefix']\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0metadata_registry = self._metadata_registry\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0def firstBatch():\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0return self.buildRecords(\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0metadata_prefix, namespaces,\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0metadata_registry, tree)\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0def nextBatch(token):\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0tree = self.makeRequestErrorHandling(\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0verb='ListRecords',\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0resumptionToken=token)\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0return self.buildRecords(\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0metadata_prefix, namespaces,\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0metadata_registry, tree)\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0return ResumptionListGenerator(firstBatch, nextBatch)\
\
\'a0\'a0\'a0\'a0def ListSets_impl(self, args, tree):\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0namespaces = self.getNamespaces()\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0def firstBatch():\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0return self.buildSets(namespaces, tree)\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0def nextBatch(token):\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0tree = self.makeRequestErrorHandling(\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0verb='ListSets',\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0resumptionToken=token)\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0return self.buildSets(namespaces, tree)\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0return ResumptionListGenerator(firstBatch, nextBatch)\
\
\'a0\'a0\'a0\'a0# various helper methods\
\
\'a0\'a0\'a0\'a0def buildRecords(self,\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0metadata_prefix, namespaces, metadata_registry, tree):\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0# first find resumption token if available\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0evaluator = etree.XPathEvaluator(tree,\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0namespaces=namespaces)\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0token = evaluator.evaluate(\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0'string(/oai:OAI-PMH/*/oai:resumptionToken/text())')\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0if token.strip() == '':\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0token = None\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0record_nodes = evaluator.evaluate(\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0'/oai:OAI-PMH/*/oai:record')\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0result = []\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0for record_node in record_nodes:\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0record_evaluator = etree.XPathEvaluator(record_node,\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0namespaces=namespaces)\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0e = record_evaluator.evaluate\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0# find header node\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0header_node = e('oai:header')[0]\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0# create header\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0header = buildHeader(header_node, namespaces)\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0# find metadata node\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0metadata_list = e('oai:metadata')\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0if metadata_list:\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0metadata_node = metadata_list[0]\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0# create metadata\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0metadata = metadata_registry.readMetadata(metadata_prefix,\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0metadata_node)\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0else:\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0metadata = None\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0# XXX TODO: about, should be third element of tuple\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0result.append((header, metadata, None))\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0return result, token\
\
\'a0\'a0\'a0\'a0def buildIdentifiers(self, namespaces, tree):\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0evaluator = etree.XPathEvaluator(tree,\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0namespaces=namespaces)\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0# first find resumption token is available\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0token = evaluator.evaluate(\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0'string(/oai:OAI-PMH/oai:ListIdentifiers/oai:resumptionToken/text())')\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0if token.strip() == '':\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0token = None\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0header_nodes = evaluator.evaluate(\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0'/oai:OAI-PMH/oai:ListIdentifiers/oai:header')\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0result = []\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0for header_node in header_nodes:\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0header = buildHeader(header_node, namespaces)\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0result.append(header)\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0return result, token\
\
\'a0\'a0\'a0\'a0def buildSets(self, namespaces, tree):\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0evaluator = etree.XPathEvaluator(tree,\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0namespaces=namespaces)\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0# first find resumption token if available\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0token = evaluator.evaluate(\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0'string(/oai:OAI-PMH/oai:ListSets/oai:resumptionToken/text())')\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0if token.strip() == '':\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0token = None\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0set_nodes = evaluator.evaluate(\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0'/oai:OAI-PMH/oai:ListSets/oai:set')\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0sets = []\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0for set_node in set_nodes:\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0e = etree.XPathEvaluator(set_node,\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0namespaces=namespaces).evaluate\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0# make sure we get back unicode strings instead\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0# of lxml.etree._ElementUnicodeResult objects.\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0setSpec = unicode(e('string(oai:setSpec/text())'))\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0setName = unicode(e('string(oai:setName/text())'))\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0# XXX setDescription nodes\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0sets.append((setSpec, setName, None))\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0return sets, token\
\
\'a0\'a0\'a0\'a0def makeRequestErrorHandling(self, **kw):\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0xml = self.makeRequest(**kw)\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0try:\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0tree = self.parse(xml)\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0except SyntaxError:\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0raise error.XMLSyntaxError(kw)\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0# check whether there are errors first\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0e_errors = tree.xpath('/oai:OAI-PMH/oai:error',\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0namespaces=self.getNamespaces())\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0if e_errors:\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0# XXX right now only raise first error found, does not\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0# collect error info\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0for e_error in e_errors:\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0code = e_error.get('code')\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0msg = e_error.text\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0if code not in ['badArgument', 'badResumptionToken',\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0'badVerb', 'cannotDisseminateFormat',\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0'idDoesNotExist', 'noRecordsMatch',\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0'noMetadataFormats', 'noSetHierarchy']:\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0raise error.UnknownError,\\\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0"Unknown error code from server: %s, message: %s" % (\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0code, msg)\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0# find exception in error module and raise with msg\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0raise getattr(error, code[0].upper() + code[1:] + 'Error'), msg\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0return tree\
\
\'a0\'a0\'a0\'a0def makeRequest(self, **kw):\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0raise NotImplementedError\
\
class Client(LibrisOAIClient):\
\'a0\'a0\'a0\'a0def __init__(\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0self, base_url, metadata_registry=None, credentials=None):\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0LibrisOAIClient.__init__(self, metadata_registry)\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0self._base_url = base_url\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0if credentials is not None:\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0self._credentials = base64.encodestring('%s:%s' % credentials)\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0else:\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0self._credentials = None\
\
\'a0\'a0\'a0\'a0def makeRequest(self, **kw):\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0"""Actually retrieve XML from the server.\
        """\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0# XXX include From header?\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0headers = \{'User-Agent': 'pyoai'\}\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0if self._credentials is not None:\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0headers['Authorization'] = 'Basic ' + self._credentials.strip()\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0request = urllib2.Request(\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0self._base_url, data=urlencode(kw), headers=headers)\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0return retrieveFromUrlWaiting(request)\
\
def buildHeader(header_node, namespaces):\
\'a0\'a0\'a0\'a0e = etree.XPathEvaluator(header_node,\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0namespaces=namespaces).evaluate\
\'a0\'a0\'a0\'a0identifier = e('string(oai:identifier/text())')\
\'a0\'a0\'a0\'a0datestamp = datestamp_to_datetime(\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0str(e('string(oai:datestamp/text())')))\
\'a0\'a0\'a0\'a0setspec = [str(s) for s in e('oai:setSpec/text()')]\
\'a0\'a0\'a0\'a0deleted = e("@deleted = 'true'")\
\'a0\'a0\'a0\'a0return common.Header(identifier, datestamp, setspec, deleted)\
\
def ResumptionListGenerator(firstBatch, nextBatch):\
\'a0\'a0\'a0\'a0result, token = firstBatch()\
\'a0\'a0\'a0\'a0while 1:\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0for item in result:\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0yield item\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0if token is None:\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0break\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0result, token = nextBatch(token)\
\
def retrieveFromUrlWaiting(request,\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0wait_max=WAIT_MAX, wait_default=WAIT_DEFAULT):\
\'a0\'a0\'a0\'a0"""Get text from URL, handling 503 Retry-After.\
    """\
\'a0\'a0\'a0\'a0for i in range(wait_max):\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0try:\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0f = urllib2.urlopen(request)\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0text = f.read()\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0f.close()\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0# we successfully opened without having to wait\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0break\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0except urllib2.HTTPError, e:\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0if e.code == 503:\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0try:\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0retryAfter = int(e.hdrs.get('Retry-After'))\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0except TypeError:\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0retryAfter = None\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0if retryAfter is None:\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0time.sleep(wait_default)\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0else:\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0time.sleep(retryAfter)\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0else:\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0# reraise any other HTTP error\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0raise\
\'a0\'a0\'a0\'a0else:\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0raise Error, "Waited too often (more than %s times)" % wait_max\
\'a0\'a0\'a0\'a0return text\
\
class ServerClient(LibrisOAIClient):\
\'a0\'a0\'a0\'a0def __init__(self, server, metadata_registry=None):\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0LibrisOAIClient.__init__(self, metadata_registry)\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0self._server = server\
\
\'a0\'a0\'a0\'a0def makeRequest(self, **kw):\
\'a0\'a0\'a0\'a0\'a0\'a0\'a0\'a0return self._server.handleRequest(kw)\
}