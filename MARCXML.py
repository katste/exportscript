from pymarc import marcxml

class MARCXMLReader(object):
    """Returns the PyMARC record from the OAI structure for MARC XML"""
    def __call__(self, element):
        handler = marcxml.XmlHandler()
        marcxml.parse_xml(StringIO(tostring(element[0])), handler)
        return handler.records[0]
