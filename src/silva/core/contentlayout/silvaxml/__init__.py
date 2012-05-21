# package
from Products.Silva.silvaxml import xmlexport, NS_SILVA_URI

NS_URI = NS_SILVA_URI + '/silva-core-contentlayout'

xmlexport.theXMLExporter.registerNamespace(
    'contentlayout', NS_URI)


