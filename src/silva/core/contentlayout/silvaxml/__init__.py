# package
from Products.Silva.silvaxml import NS_SILVA_URI
from Products.Silva.silvaxml.xmlexport import registerNamespace

NS_URI = NS_SILVA_URI + '/silva-core-contentlayout'

registerNamespace('contentlayout', NS_URI)


