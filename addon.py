import sys
import urlparse
import urllib, urllib2, xbmcplugin, xbmcaddon, xbmcgui, string, htmllib, os, platform, random, calendar, re
import CommonFunctions
import xml.etree.ElementTree as ElementTree 

addonId = 'plugin.video.playonbrowser'
addonVersion = '1.0.0'


lib_path = xbmcaddon.Addon(addonId). \
    getAddonInfo('path') + '/resources/lib/' 
sys.path.append(lib_path) 
import m3u8

baseUrl = sys.argv[0]
addonHandle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])
print baseUrl
print addonHandle
print args

# playonInternalUrl = 'http://m.playon.tv/'
# need to move to config. 

settings = xbmcaddon.Addon(id=addonId)
playonInternalUrl = settings.getSetting("playonserver").rstrip('/')
playonDataPath = '/data/data.xml'

xbmcplugin.setContent(addonHandle, 'movies')


common = CommonFunctions
common.plugin = addonId + '-' + addonVersion




""" 
-----------------------------------
   Internal Functions 
-----------------------------------
""" 

def BuildUrl(query):
    return baseUrl + '?' + urllib.urlencode(query)

def BuildPlayonUrl(href = ""):
    if not href:
        return playonInternalUrl + playonDataPath
    else:
        return playonInternalUrl + href
    
def buildMenu():
    url = playonInternalUrl 
    response = urllib.urlopen(url)
    if response and response.getcode() == 200:
        content = response.read()
        print content
    else:
        xbmcgui.Dialog().ok(addonId, 'Could not open URL %s to create menu' % (url))

def getXml(url):
    try:
        print addonId + ':  getXml: '+ url
        usock = urllib2.urlopen(url)
        response = usock.read()
        usock.close()
        return ElementTree.fromstring(response)
    except: return False 

def getHtml( url , useCookie=False):
    try:
        print addonId + ':  getHtml: '+ url
        usock = urllib2.urlopen(url)
        response = usock.read()
        usock.close()
        return response
    except: return False 

""" 
-----------------------------------
   Main Loop
-----------------------------------
""" 
def getArgumentValue(name):
    if args.get(name, None) is None:
        return None
    else:
        return args.get(name, None)[0]

mode = getArgumentValue('mode')
foldername = getArgumentValue('foldername')
href = getArgumentValue('href')

def generateListItems(xml,href):
    for group in xml.getiterator('group'):
        if group.attrib.get('href') == href:
            continue
        name = group.attrib.get('name').encode('ascii', 'ignore')
        url = BuildUrl({'mode': group.attrib.get('type'), 'foldername': name, 'href': group.attrib.get('href'), 'parenthref': href})
        if group.attrib.get('art') == None:
            image = 'DefaultVideo.png'
        else:
            image = playonInternalUrl + group.attrib.get('art')
            
        if group.attrib.get('type') == 'folder':
            li = xbmcgui.ListItem(name, iconImage=image, thumbnailImage=image)
            xbmcplugin.addDirectoryItem(handle=addonHandle, url=url, listitem=li, isFolder=True)
        elif group.attrib.get('type') == 'video':
            playonUrl = BuildPlayonUrl(group.attrib.get('href'))
            mediaXml = getXml(playonUrl)
            mediaNode = mediaXml.find('media')
            src = mediaNode.attrib.get('src')
            url =  playonInternalUrl + '/' + src
            li = xbmcgui.ListItem(name, iconImage=image, thumbnailImage=image)
            li.setInfo('video', { 'plotoutline': group.attrib.get('description'),
                      'title': name})
            xbmcplugin.addDirectoryItem(handle=addonHandle, url=url, listitem=li)
            
    xbmcplugin.endOfDirectory(addonHandle)

#building the main menu... Replicate the XML structure. 
if mode is None:
    playonUrl = BuildPlayonUrl()
    xml = getXml(playonUrl)
    print " Building top menu"
    displayCategories = {'MoviesAndTV': 3,'News': 4,'Sports': 8,'Kids': 16,'Music': 32,'VideoSharing': 64,'Comedy': 128,'MyMedia': 256,'Plugins': 512,'Other': 1024,'LiveTV': 2048}
    displayTitles = {'MoviesAndTV': 'Movies And TV','News': 'News','Sports': 'Sports','Kids': 'Kids','Music': 'Music','VideoSharing': 'Video Sharing','Comedy': 'Comedy','MyMedia': 'My Media','Plugins': 'Plugins','Other': 'Other','LiveTV': 'Live TV'}
    displayImages = {'MoviesAndTV': '/images/categories/movies.png','News': '/images/categories/news.png','Sports': '/images/categories/sports.png','Kids': '/images/categories/kids.png','Music': '/images/categories/music.png','VideoSharing': '/images/categories/videosharing.png','Comedy': '/images/categories/comedy.png','MyMedia': '/images/categories/mymedia.png','Plugins': '/images/categories/plugins.png','Other': '/images/categories/other.png','LiveTV': '/images/categories/livetv.png'}
    
    for key, value in sorted(displayCategories.iteritems(), key=lambda (k,v): (v,k)):
        url = BuildUrl({'mode': 'category', 'category':displayCategories[key]})
        li = xbmcgui.ListItem(displayTitles[key], iconImage=playonInternalUrl + displayImages[key], thumbnailImage=playonInternalUrl + displayImages[key])
        xbmcplugin.addDirectoryItem(handle=addonHandle, url=url, listitem=li, isFolder=True)
    
    xbmcplugin.endOfDirectory(addonHandle)
elif mode == 'category':
    playonUrl = BuildPlayonUrl()
    xml = getXml(playonUrl)
    category = getArgumentValue('category')
    
    print " Building "+category+" menu"
    
    for group in xml.getiterator('group'):
        if group.attrib.get('category') == None:
            nodeCat = 1024
        else:
            nodeCat = group.attrib.get('category')
        
        if int(nodeCat) & int(category) != 0:
            name = group.attrib.get('name').encode('ascii', 'ignore')
            url = BuildUrl({'mode': group.attrib.get('type'), 'foldername': name, 'href': group.attrib.get('href')})
            if group.attrib.get('art') == None:
                image = 'DefaultVideo.png'
            else:
                image = playonInternalUrl + group.attrib.get('art')
                li = xbmcgui.ListItem(name, iconImage=image, thumbnailImage=image)
                xbmcplugin.addDirectoryItem(handle=addonHandle, url=url, listitem=li, isFolder=True)
    xbmcplugin.endOfDirectory(addonHandle)
elif mode == 'folder':
    playonUrl = BuildPlayonUrl(href)
    xml = getXml(playonUrl)
    print "In a folder:" + foldername + "::" + href
    generateListItems(xml,href)

    



        

