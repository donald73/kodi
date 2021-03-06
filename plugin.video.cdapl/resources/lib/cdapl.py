# -*- coding: utf-8 -*-
"""
Created on Thu Feb 11 18:47:43 2016

@author: ramic
"""

import urllib2
import re
import json as json

import jsunpack as jsunpack

BASEURL='http://www.cda.pl'
TIMEOUT = 5

def getUrl(url,data=None,cookies=None):
    req = urllib2.Request(url,data)
    req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.97 Safari/537.36')
    if cookies:
        req.add_header("Cookie", cookies)
    try:
        response = urllib2.urlopen(req,timeout=TIMEOUT)
        link =  response.read()
        response.close()
    except:
        link=''
    return link


##  JSONUNPACK

#        result = getUrl(url)
#        result = re.compile('(eval.*?)\n').findall(result)[-1]
#        result = unpack(result)

def _get_encoded_unpaker(content):
    src =''
    packed = re.compile('(eval.function.*?\)\))\n',re.DOTALL).findall(content)
    if packed:
        packed=re.sub('  ',' ',packed[0])
        packed=re.sub('\n','',packed)
        try:
            unpacked = jsunpack.unpack(packed)
        except:
            unpacked=''
        if unpacked:
            unpacked=re.sub(r'\\',r'',unpacked)
            src1 = re.compile('file:\s*[\'"](.+?)[\'"],',  re.DOTALL).search(unpacked)
            src2 = re.compile('url:\s*[\'"](.+?)[\'"],',  re.DOTALL).search(unpacked)
            if src1:
                src = src1.group(1)
            elif src2:
                src = src2.group(1)
    return src

def _get_encoded(content):
    src=''
    idx1 = content.find('|||http')
    if idx1>0:
        idx2 = content.find('.split',idx1)
        encoded =content[idx1:idx2]
        if encoded:
            #print encoded
            tmp = encoded.split('player')[0]
            tmp=re.sub(r'[|]+\w{2,3}[|]+','|',tmp,re.DOTALL)
            tmp=re.sub(r'[|]+\w{2,3}[|]+','|',tmp,re.DOTALL)
            
            
            remwords=['http','cda','pl','logo','width','height','true','static','st','mp4','false','video','static',
                    'type','swf','player','file','controlbar','ads','czas','position','duration','bottom','userAgent',
                    'match','png','navigator','id', '37', 'regions', '09', 'enabled', 'src', 'media']
            remwords=['http', 'logo', 'width', 'height', 'true', 'static', 'false', 'video', 'player', 
                'file', 'type', 'regions', 'none', 'czas', 'enabled', 'duration', 'controlbar', 'match', 'bottom',
                'center', 'position', 'userAgent', 'navigator', 'config', 'html', 'html5', 'provider', 'black',
                'horizontalAlign', 'canFireEventAPICalls', 'useV2APICalls', 'verticalAlign', 'timeslidertooltipplugin', 
                'overlays', 'backgroundColor', 'marginbottom', 'plugins', 'link', 'stretching', 'uniform', 'static1', 
                'setup', 'jwplayer', 'checkFlash', 'SmartTV', 'v001', 'creme', 'dock', 'autostart', 'idlehide', 'modes',
               'flash', 'over', 'left', 'hide', 'player5', 'image', 'KLIKNIJ', 'companions', 'restore', 'clickSign',
                'schedule', '_countdown_', 'countdown', 'region', 'else', 'controls', 'preload', 'oryginalne', 'style', 
                '620px', '387px', 'poster', 'zniknie', 'sekund', 'showAfterSeconds', 'images', 'Reklama', 'skipAd',
                 'levels', 'padding', 'opacity', 'debug', 'video3', 'close', 'smalltext', 'message', 'class', 'align',
                  'notice', 'media']

            for one in remwords:
                tmp=tmp.replace(one,'')
            
            cleanup=tmp.replace('|',' ').split()
            
            out={'server': '', 'e': '', 'file': '', 'st': ''}
            if len(cleanup)==4:
                print 'Length OK'
                for one in cleanup:
                    if one.isdigit():
                        out['e']=one
                    elif re.match('[a-z]{2,}\d{3}',one) and len(one)<10:  
                        out['server'] = one
                    elif len(one)==22:
                        out['st'] = one
                    else:
                        out['file'] = one
                src='http://%s.cda.pl/%s.mp4?st=%s&e=%s'%(out.get('server'),out.get('file'),out.get('st'),out.get('e'))
    return src

# url='http://www.cda.pl/video/49982323?wersja=720p'
# content = getUrl(url)

def scanforVideoLink(content):
    """
    Scans for video link included encoded one
    """
    video_link=''
    src1 = re.compile('file: [\'"](.+?)[\'"],',  re.DOTALL).search(content)
    src2 = re.compile('url: [\'"](.+?)[\'"],',  re.DOTALL).search(content)
    if src1:
        print 'found RE [file:]'
        video_link = src1.group(1)
    elif src2:
        print 'found RE [url:]'
        video_link = src2.group(1)
    else:
        print 'encoded : unpacker'
        video_link = _get_encoded_unpaker(content)
        if not video_link:
            print 'encoded : force '
            video_link = _get_encoded(content)
    return video_link


  
def getVideoUrls(url,tryIT=4):
    """
    returns 
        - ulr http://....
        - or list of [('720p', 'http://www.cda.pl/video/1946991f?wersja=720p'),...]
         
    """  
    # check if version is selecte
    playerSWF1='|Cookie="PHPSESSID=1&Referer=http://static.cda.pl/player5.9/player.swf'
    playerSWF='|Referer=http://static.cda.pl/player5.9/player.swf'
    print url
    content = getUrl(url)
    src=[]
    if not '?wersja' in url:
         quality_options = re.compile('<a data-quality="(.*?)" (?P<H>.*?)>(?P<Q>.*?)</a>', re.DOTALL).findall(content)
         for quality in quality_options:
             link = re.search('href="(.*?)"',quality[1])
             hd = quality[2]
             src.insert(0,(hd,BASEURL+link.group(1)))
    if not src:     # no qualities availabe ... get whaterer is there
        src = scanforVideoLink(content)
        if src:
            src+=playerSWF1+playerSWF
        else:
            for i in range(tryIT):
                print 'Trying get link %d' %i
                print url
                content = getUrl(url)
                src = scanforVideoLink(content)
                if src: 
                    src+=playerSWF1+playerSWF
                    break
    return src    


def getVideoUrlsQuality(url,quality=0):
    """
    returns url to video
    """
    src = getVideoUrls(url)
    if type(src)==list:
        selected=src[quality]
        print 'Quality :',selected[0]
        src = getVideoUrls(selected[1])
    return src
    


def _scan_UserFolder(urlF,recursive=True,items=[],folders=[]):
    content = getUrl(urlF)
    items = items
    folders = folders
    
    match   = re.compile('<a href="(.*?)">(.*?)</a> <span class="hidden-viewTiles">(.*?)</span>').findall(content)
    matchT  = re.compile('class="time-thumb-fold">(.*?)</span>').findall(content)
    matchHD = re.compile('class="thumbnail-hd-ico">(.*?)</span>').findall(content)
    matchHD = [a.replace('<span class="hd-ico-elem">','') for a in matchHD]
    matchIM = re.compile('<img[ \t\n]+class="thumb thumb-bg thumb-size"[ \t\n]+alt="(.*?)"[ \t\n]+src="(.*?)">',re.DOTALL).findall(content)
    
    print 'Video #%d' %(len(match))

    for i in range(len(match)):
        url = BASEURL+ match[i][0]
        title = unicodePLchar(match[i][1])
        duration =  sum([a*b for a,b in zip([3600,60,1], map(int,matchT[i].split(':')))]) / 60.0
        code = matchHD[i]
        plot = unicodePLchar(matchIM[i][0])
        img = matchIM[i][1]
        items.append({'url':url,'title':unicode(title,'utf-8'),'code':code.encode('utf-8'),'plot':unicode(plot,'utf-8'),'img':img,'duration':duration})
    
    # Folders
    folders_links = re.compile('class="folder-area">[ \t\n]+<a[ \t\n]+href="(.*?)"',re.DOTALL).findall(content)
    folders_names = re.compile('<span[ \t\n]+class="name-folder">(.*?)</span>',re.DOTALL).findall(content)
    if folders_links:
        if len(folders_names) > len(folders_links): folders_names = folders_names[1:]   # remove parent folder is exists
        for i in range(len(folders_links)):
            folders.append( {'url':folders_links[i],'title': html_entity_decode(folders_names[i]) })
    print 'Folder #%d ' %(len(folders_links))
    
    nextpage = re.compile('<div class="paginationControl">[ \t\n]+<a class="btn btn-primary block" href="(.*?)"',re.DOTALL).findall(content)
    
    if recursive and len(nextpage):
        print 'Entering next page: ', nextpage[0]
        _scan_UserFolder(nextpage[0],recursive,items)
    
    return items,folders
  
   
def get_UserFolder_content( urlF,recursive=True,filtr_items={}):
    items=[]
    folders=[]
    items,folders=_scan_UserFolder(urlF,recursive,items,folders)
    _items=[]
    if filtr_items:
        cnt=0
        key = filtr_items.keys()[0]
        value = filtr_items[key].encode("utf-8")
        for item in items:
            if value in item.get(key):
                cnt +=1
                _items.append(item)
        items = _items
        print 'Filted %d items by [%s in %s]' %(cnt, value, key)
    return items,folders
    


## JSON TASK

import htmlentitydefs

def html_entity_decode_char(m):
    ent = m.group(1)
    if ent.startswith('x'):
        return unichr(int(ent[1:],16))
    try:
        return unichr(int(ent))
    except Exception, exception:
        if ent in htmlentitydefs.name2codepoint:
            return unichr(htmlentitydefs.name2codepoint[ent])
        else:
            return ent

def html_entity_decode( string):
    string = string.decode('UTF-8')
    s = re.compile("&#?(\w+?);").sub(html_entity_decode_char, string)
    return s.encode('UTF-8')
    
    
def ReadJsonFile(jfilename):
    if jfilename.startswith('http'):
        content = getUrl(jfilename)
    else: # local content
        with open(jfilename,'r') as f:
            content =  f.read()
    data=json.loads(html_entity_decode(content))
    #data=json.loads(content)
    return data

def xpath(mydict, path=''):
    elem = mydict
    if path:
        try:
            for x in path.strip("/").split("/"):
                elem = elem.get( x.decode('utf-8') )
        except:
            pass
    return elem
    
def jsconWalk(data,path):
    lista_katalogow = []
    lista_pozycji=[]
    
    elems = xpath(data,path) 
    if type(elems) is dict:
        # created directory
        for e in elems.keys():
            one=elems.get(e)
            if type(one) is str or type(one) is unicode:    # another json file
                lista_katalogow.append( {'img':'','title':e,'url':"", "jsonfile" :one} )
            else:
                if isinstance(e, unicode):
                    e = e.encode('utf8')
                elif isinstance(e, str):
                    # Must be encoded in UTF-8
                    e.decode('utf8')
                lista_katalogow.append( {'img':'','title':e,'url':path+'/'+e,'fanart':''} )
    
    if type(elems) is list:
        print 'List items'
        for one in elems:
            # check if direct link or User folder:
            if one.has_key('url'):
                lista_pozycji.append( one )
            elif one.has_key('folder'):        #This is folder in cds.pl get content:
                filtr_items = one.get('flter_item',{})
                show_subfolders = one.get('subfoders',True)
                show_items = one.get('items',True)
                is_recursive = one.get('recursive',True)
                
                items,folders = get_UserFolder_content( 
                                        urlF        = one.get('folder',''),
                                        recursive   = is_recursive,
                                        filtr_items = filtr_items )
                if show_subfolders:
                    lista_katalogow.extend(folders)
                if show_items:
                    lista_pozycji.extend(items)
                
    return (lista_pozycji,lista_katalogow)
    


def unicodePLchar(txt):
    txt = txt.replace('#038;','')
    txt = txt.replace('&lt;br/&gt;',' ')
    txt = txt.replace('&#34;','"')
    txt = txt.replace('&#39;','\'').replace('&#039;','\'')
    txt = txt.replace('&#8221;','"')
    txt = txt.replace('&#8222;','"')
    txt = txt.replace('&#8211;','-').replace('&ndash;','-')
    txt = txt.replace('&quot;','"').replace('&amp;quot;','"')
    txt = txt.replace('&oacute;','ó').replace('&Oacute;','Ó')
    txt = txt.replace('&amp;oacute;','ó').replace('&amp;Oacute;','Ó')
    #txt = txt.replace('&amp;','&')
    txt = txt.replace('\u0105','ą').replace('\u0104','Ą')
    txt = txt.replace('\u0107','ć').replace('\u0106','Ć')
    txt = txt.replace('\u0119','ę').replace('\u0118','Ę')
    txt = txt.replace('\u0142','ł').replace('\u0141','Ł')
    txt = txt.replace('\u0144','ń').replace('\u0144','Ń')
    txt = txt.replace('\u00f3','ó').replace('\u00d3','Ó')
    txt = txt.replace('\u015b','ś').replace('\u015a','Ś')
    txt = txt.replace('\u017a','ź').replace('\u0179','Ź')
    txt = txt.replace('\u017c','ż').replace('\u017b','Ż')
    return txt