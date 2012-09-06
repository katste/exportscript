from pymarc import marcxml
from cStringIO import StringIO
from lxml.etree import tostring, XPathEvaluator

class MARCXMLReader(object):
    """Returns the PyMARC record from the OAI structure for MARC XML"""
    def __call__(self, element):
        handler = marcxml.XmlHandler()
        marcxml.parse_xml(StringIO(tostring(element[0])), handler)
        return marcxml.record_to_xml(handler.records[0], namespace=True)

