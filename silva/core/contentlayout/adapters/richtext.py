#python
import re
from lxml import html, etree
from urlparse import urlparse
from types import UnicodeType

#zope 3
from five import grok

#silva imports
from silva.core.interfaces.adapters import IPath
from silva.core.interfaces import ISilvaObject, IImage

#from bethel.core.zopecache import silva

#local
from silva.core.contentlayout.interfaces import (IRichTextCleanup,
                                                 ITinyMCEField)

#for the mailto: pattern see the description of the email addressing
#format in the RFC 2822: http://tools.ietf.org/html/rfc2822#section-3.4.1
# so much more is allowed everywhere in the email address.  The RE currently
# only searches the full list of chars for the LHS of the address.  It does
# not support "quoted strings".
URL_PATTERN = r'(((http|https|ftp|news|itms|webcal|tel)://([A-Za-z0-9%\-_]+(:[A-Za-z0-9%\-_]+)?@)?([A-Za-z0-9\-]+\.)+[A-Za-z0-9]+)(:[0-9]+)?(/([A-Za-z0-9\-_\?!@#$%^&*/=\.]+[^\.\),;\|])?)?|(javascript:.+?)|(mailto:[A-Za-z0-9!#\$%\&\'\*\+\-\/=\?\^_`\{\}\|~\.]+@([A-Za-z0-9\-]+\.)+[A-Za-z0-9]+)|(http|https|ftp|news|itms|webcal|tel)://localhost(:[0-9]+)?(/([A-Za-z0-9\-_\?!@#$%^&*/=\.]+[^\.\),;\|])?))'
_url_match = re.compile(URL_PATTERN)


class TinyMCERichText(grok.Adapter):
    #adapter to translate tinymce xhtml for editing and public viewing
    grok.implements(IRichTextCleanup)
    grok.context(ITinyMCEField)

    def from_editor(self, text):
        """convert text submitted by tinymce into html suitable for storage.
        This will find all links in the text and send them through the
        path adapter"""
        els = html.fragments_fromstring(text)
        if len(els) == 0:
            return ''
        pad = IPath(self.context.REQUEST)
        if len(els) > 1:
            doc = html.Element('div')
            doc.extend(els)
        else:
            doc = els[0]
        for (el, attr, link, pos) in doc.iterlinks():
            if attr in ('href','src'):
                #XXX with reference mgmt, these urls will be converted to IntIds
                #
                #this sanitizes relative urls in a vhosting environment
                # but only do it if it isn't already an abs url
                if not _url_match.match(link):
                    link = pad.urlToPath(unicode(link))
                el.set(attr,link)
        if doc.tag == 'div':
            text = ''.join([etree.tostring(n, encoding='utf-8', method='html') for n in doc.getchildren() ])
        else:
            text = etree.tostring(doc, encoding='utf-8', method='html')
        return text
    
    def to_editor(self, text):
        if not text:
            return ""
        els = html.fragments_fromstring(text)
        model = self._resolve_model()
        request_pad = IPath(self.context.REQUEST)
        if len(els) > 1:
            doc = html.Element('div')
            doc.extend(els)
        else:
            doc = els[0]
        for root in els:
            for node in root.xpath('//img'):
                link = node.get('src')
                obj = None
                if link:
                    parsed = urlparse(link)
                    #if src is an absolute url, skip over it
                    if parsed[0]:
                        continue
                    #translate the path (i.e. parsed[2])
                    src = request_pad.urlToPath(parsed[2])
                    #the links coming back from tinymce (at least within the CLE
                    # are relative to the container, not the page.  However, 
                    # restrictedTraverse starts with the page, so an addition
                    # ../ needs to be prefixed to the src so that the resolved
                    # object is what is expected (otherwise it will be one level
                    # lower).  A src of '../' really means (from the Page)
                    # 'one level above the container of the page
                    if src.startswith('../'):
                        src = '../' + src
                    obj = model.unrestrictedTraverse(src.split('/'), None)
                    if obj and IImage.providedBy(obj):
                        title = obj.get_title()
                        #update the title and update the dimensions
                        node.set('title', title)
                        node.set('alt', title)
                        #get the correct image format from the SilvaImage
                        # send it in kwargs, but only if it isn't 'webformat'
                        # (which isn't a supported parameter).  This way it's
                        # easier to pass in the correct params, rather than
                        # using multiple if statements.
                        img_format = parsed[4]
                        kw = {}
                        if img_format in ('thumbnail','hires'):
                            #parameters cannot be unicode
                            if isinstance(img_format, UnicodeType):
                                img_format = str(img_format)
                            kw[img_format] = True
                        (img, imgsrc) = obj._get_image_and_src(**kw)
                        width, height = obj.getDimensions(img)
                        node.set('width', str(width))
                        node.set('height', str(height))
                else:
                    #don't adjust links, etc.
                    pass
        if doc.tag == 'div':
            text = ''.join([etree.tostring(n, encoding='utf-8', method='html') for n in doc.getchildren() ])
        else:
            text = etree.tostring(doc, encoding='utf-8', method='html')
        return text
    
    #@silva.codesourcecache()
    #(900, key_with_params=True, func_in_class=True,
    #                  include_model_path=True)
    def to_public(self, text, model, version):
        els = html.fragments_fromstring(text)
        request_pad = IPath(self.context.REQUEST)
        if len(els) > 1:
            doc = html.Element('div')
            doc.extend(els)
        else:
            doc = els[0]
        for root in els:
            for node in root.xpath('//img|//a'):
                link = node.get('src') or node.get('href')
                obj = None
                if link:
                    parsed = urlparse(link)
                    #if src is an absolute url, skip over it
                    if parsed[0]:
                        continue
                    #translate the path (i.e. parsed[2])
                    src = request_pad.urlToPath(parsed[2])
                    #the links coming back from tinymce (at least within the CLE
                    # are relative to the container, not the page.  However, 
                    # restrictedTraverse starts with the page, so an addition
                    # ../ needs to be prefixed to the src so that the resolved
                    # object is what is expected (otherwise it will be one level
                    # lower).  A src of '../' really means (from the Page)
                    # 'one level above the container of the page
                    if src.startswith('../'):
                        src = '../' + src
                    obj = model.unrestrictedTraverse(src.split('/'), None)
                    if obj and ISilvaObject.providedBy(obj):
                        if node.tag == 'img' and IImage.providedBy(obj):
                            title = obj.get_title()
                            node.set('title', title)
                            node.set('alt', title)
                            ourl = obj.absolute_url()
                            if parsed[4] and parsed[4] != 'webformat':
                                ourl += '?' + parsed[4]
                            node.set('src', ourl)
                            
                            omo = node.get('onmouseover')
                            if omo:
                                omo_link = re.search("this.src='(.*)'",omo).group(1)
                                omo_parsed = urlparse(omo_link)
                                if omo_parsed[0]:
                                    continue
                                omo_src = request_pad.urlToPath(omo_parsed[2])
                                omo_obj = model.unrestrictedTraverse(omo_src.split('/'), None)
                                if omo_obj and IImage.providedBy(omo_obj):
                                    omo_url = omo_obj.absolute_url()
                                    node.set('onmouseover',omo.replace(omo_link, omo_url))
                            omo = node.get('onmouseout')
                            if omo:
                                node.set('onmouseout', omo.replace(link, ourl))
                            #get the correct image format from the SilvaImage
                            # send it in kwargs, but only if it isn't 'webformat'
                            # (which isn't a supported parameter).  This way it's
                            # easier to pass in the correct params, rather than
                            # using multiple if statements.
                            img_format = parsed[4]
                            kw = {}
                            if img_format in ('thumbnail','hires'):
                                #parameters cannot be unicode
                                if isinstance(img_format, UnicodeType):
                                    img_format = str(img_format)
                                kw[img_format] = True
                            (img, imgsrc) = obj._get_image_and_src(**kw)
                            width, height = obj.getDimensions(img)
                            node.set('width', str(width))
                            node.set('height', str(height))
                        elif node.tag == 'a':
                            #adjust 'href'
                            node.set('href',obj.absolute_url() + (parsed[5] and '#' + parsed[5] or ''))
                else:
                    #don't adjust links, etc.
                    pass

        #Sometimes when content is copy and pasted into the rich text editor, the surrounding
        #dynamically generated HTML used by the CLE is also copied and saved. This breaks the
        #editor by preventing the edit and delete buttons from appearing. So strip the extra
        #divs out of the result (identified by their classes).
        for node in doc.xpath('//div[@class]'):
            if node.get('class') == 'bd' or node.get('class') == 'part-content' \
               or re.search('yui-module', node.get('class')):
                node.drop_tag()

        #fp case 97570 -- etree.tostring default to xml, which will convert
        # <a name="X"></a> into <a name="X" />.  Unfortunately, browsers tread
        # this tag similarly to <style> in that it needs an explicit closing tag.
        # closing inline will not work (the rest of the page will be a hyperlink).
        # For this reason, the xml method cannot be used, and we need to
        # output html instead.  This has the side-effect of needing to be 
        # translated back into x(h)tml in order to process it with xslt.
        # the uPortal/luminis webproxy channel needs xhtml, but it has an
        # html tidy option (which should be used)
        if doc.tag == 'div':
            text = ''.join([etree.tostring(n, encoding='utf-8', method='html') for n in doc.getchildren() ])
        else:
            text = etree.tostring(doc, encoding='utf-8', method='html')
        return text
    
    def _resolve_model(self):
        """first return REQUEST.model (if present), then returns 
           closest silva-related object (ISilvaObject)
           from REQUEST.parents.  If none found, returns self.context,
           which is a formulator field.
           
           Usually I expect REQUEST.parents to be used.  But if a Page has
           a Page Asset embedded it it, and the Page Asset has rich text,
           the 'model' to use is not necessarily in REQUEST.parents.  Relative
           links need to be resolved from the Page Asset.  At this time, the only
           what aaltepet knows how to do this is by setting REQUEST.model in
           the Page Asset.
           
           XXX I expect this will change / become easier with silva 2.3 and
               a full grok implementation of contentlayout
           """
        if hasattr(self.context.REQUEST, 'model'):
            return self.context.REQUEST.model
           
        parents = self.context.REQUEST.get('PARENTS',[])
        if not parents:
            return self.context
        
        for p in parents:
            if ISilvaObject.providedBy(p):
                return p
        return self.context
