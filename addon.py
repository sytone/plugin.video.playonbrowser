import sys
import urlparse
import urllib
import urllib2
import xbmc
import xbmcplugin
import xbmcaddon
import xbmcgui
import string
import htmllib
import os
import platform
import random
import calendar
import re
import CommonFunctions
import xml.etree.ElementTree as ElementTree 

# 
#   Set-up global variables
addonId = 'plugin.video.playonbrowser'
addonVersion = '1.0.0'
mediaPath = xbmcaddon.Addon(addonId).getAddonInfo('path') + '/resources/media/' 
playonDataPath = '/data/data.xml'

#
#   Pull the arguments in. 
baseUrl = sys.argv[0]
addonHandle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])

#
#   Pull the settings in. 
settings = xbmcaddon.Addon(id=addonId)
playonInternalUrl = settings.getSetting("playonserver").rstrip('/')
debug = settings.getSetting("debug")

#
#   Set-up some KODI defaults. 
xbmcplugin.setContent(addonHandle, 'movies')
common = CommonFunctions
common.plugin = addonId + '-' + addonVersion

#
#   Internal Functions 
#
def log_message(msg, information = False):
    """ Simple logging helper. """
    if (information or debug) and isinstance(msg, str):
        print addonId + "::" + addonVersion + ": " + msg
    elif (information or debug):
        print addonId + "::" + addonVersion + "... \/ ..."
        print msg
        
def build_url(query):
    """ This will build and encode the URL for the addon. """
    log_message('build_url... \/ ...')
    log_message(query)
    return baseUrl + '?' + urllib.urlencode(query)

def build_playon_url(href = ""):
    """ This will generate the correct URL to access the XML pushed out by the machine running playon. """
    log_message('build_playon_url: '+ href)
    if not href:
        return playonInternalUrl + playonDataPath
    else:
        return playonInternalUrl + href
    
def get_xml(url):
    """ This will pull down the XML content and return a ElementTree. """
    try:
        log_message('get_xml: '+ url)
        usock = urllib2.urlopen(url)
        response = usock.read()
        usock.close()
        return ElementTree.fromstring(response)
    except: return False 

def get_argument_value(name):
    """ pulls a value out of the passed in arguments. """
    if args.get(name, None) is None:
        return None
    else:
        return args.get(name, None)[0]

def generate_list_items(xml, href, foldername, nametree):
    """ Will generate a list of directory items for the UI based on the xml values. """
    for group in xml.getiterator('group'):
        if group.attrib.get('href') == href:
            continue
        
        # Build up the name tree. 
        name = group.attrib.get('name').encode('ascii', 'ignore')
        url = build_url({'mode': group.attrib.get('type'), 
                            'foldername': name, 
                            'href': group.attrib.get('href'), 
                            'parenthref': href, 
                            'nametree': nametree + '/' + name})
        
        if group.attrib.get('art') == None:
            image = 'DefaultVideo.png'
        else:
            image = playonInternalUrl + group.attrib.get('art')
            
        if group.attrib.get('type') == 'folder':
            li = xbmcgui.ListItem(name, iconImage=image, thumbnailImage=image)
            xbmcplugin.addDirectoryItem(handle=addonHandle, url=url, listitem=li, isFolder=True)
        elif group.attrib.get('type') == 'video':
            playonUrl = build_playon_url(group.attrib.get('href'))
            mediaXml = get_xml(playonUrl)
            mediaNode = mediaXml.find('media')
            li = xbmcgui.ListItem(name, iconImage=image, thumbnailImage=image)
            li.setInfo('video', { 'plotoutline': group.attrib.get('description'), 'title': name})
            xbmcplugin.addDirectoryItem(handle=addonHandle, url=url, listitem=li)
            
    xbmcplugin.endOfDirectory(addonHandle)


#
#    Main Loop

log_message("Base URL:" + baseUrl, True)
log_message("Addon Handle:" + str(addonHandle), True)
log_message("Arguments", True)
log_message(args, True)

# Pull out the URL arguments for usage. 
mode = get_argument_value('mode')
foldername = get_argument_value('foldername')
nametree = get_argument_value('nametree')
href = get_argument_value('href')

if mode is None: #building the main menu... Replicate the XML structure. 
    playonUrl = build_playon_url()
    xml = get_xml(playonUrl)
    log_message("Building top menu")
    displayCategories = {'MoviesAndTV': 3,'News': 4,'Sports': 8,'Kids': 16,'Music': 32,'VideoSharing': 64,'Comedy': 128,'MyMedia': 256,'Plugins': 512,'Other': 1024,'LiveTV': 2048}
    displayTitles = {'MoviesAndTV': 'Movies And TV','News': 'News','Sports': 'Sports','Kids': 'Kids','Music': 'Music','VideoSharing': 'Video Sharing','Comedy': 'Comedy','MyMedia': 'My Media','Plugins': 'Plugins','Other': 'Other','LiveTV': 'Live TV'}
    displayImages = {'MoviesAndTV': '/images/categories/movies.png','News': '/images/categories/news.png','Sports': '/images/categories/sports.png','Kids': '/images/categories/kids.png','Music': '/images/categories/music.png','VideoSharing': '/images/categories/videosharing.png','Comedy': '/images/categories/comedy.png','MyMedia': '/images/categories/mymedia.png','Plugins': '/images/categories/plugins.png','Other': '/images/categories/other.png','LiveTV': '/images/categories/livetv.png'}
    
    for key, value in sorted(displayCategories.iteritems(), key=lambda (k,v): (v,k)):
        url = build_url({'mode': 'category', 'category':displayCategories[key]})
        li = xbmcgui.ListItem(displayTitles[key], iconImage=playonInternalUrl + displayImages[key], thumbnailImage=playonInternalUrl + displayImages[key])
        xbmcplugin.addDirectoryItem(handle=addonHandle, url=url, listitem=li, isFolder=True)
    
    xbmcplugin.endOfDirectory(addonHandle)
elif mode == 'category': # Category has been selected, build a list of items under that category. 
    playonUrl = build_playon_url()
    xml = get_xml(playonUrl)
    category = get_argument_value('category')
    
    log_message("Building "+category+" menu")
    
    for group in xml.getiterator('group'):
        if group.attrib.get('category') == None:
            nodeCat = 1024
        else:
            nodeCat = group.attrib.get('category')
        
        if int(nodeCat) & int(category) != 0:
            name = group.attrib.get('name').encode('ascii', 'ignore')
            url = build_url({'mode': group.attrib.get('type'), 'foldername': name, 'href': group.attrib.get('href'), 'nametree': name})
            if group.attrib.get('art') == None:
                image = 'DefaultVideo.png'
            else:
                image = playonInternalUrl + group.attrib.get('art')
                li = xbmcgui.ListItem(name, iconImage=image, thumbnailImage=image)
                xbmcplugin.addDirectoryItem(handle=addonHandle, url=url, listitem=li, isFolder=True)
    xbmcplugin.endOfDirectory(addonHandle)
elif mode == 'folder': # General folder handling. 
    playonUrl = build_playon_url(href)
    xml = get_xml(playonUrl)
    log_message("In a folder:" + foldername + "::" + href + "::" + nametree)
    generate_list_items(xml, href, foldername, nametree)
elif mode == 'video' : # Video link from Addon or STRM. Parse and play. 
    """ We are doing a manual play to handle the id change during playon restarts. """
    log_message("In a video:" + foldername + "::" + href + "::" + nametree)
    # Run though the name tree! No restart issues but slower.
    playonUrl = build_playon_url()
    xml = get_xml(playonUrl)
    nametreelist = nametree.split('/')
    roothref = None
    for group in xml.getiterator('group'):
        if group.attrib.get('name') == nametreelist[0]:
            roothref = group.attrib.get('href')

    if roothref != None:
        for i, v in enumerate(nametreelist):
            log_message("Level:" + str(i) + " Value:" + v)
            if i != 0:
                playonUrl = build_playon_url(roothref)
                xml = get_xml(playonUrl)
                for group in xml.getiterator('group'):
                    if group.attrib.get('name') == v:
                        roothref = group.attrib.get('href')
                        type = group.attrib.get('type')
                        if type == 'video':
                            # End of tree! I thinks. 
                            playonUrl = build_playon_url(group.attrib.get('href'))
                            name = group.attrib.get('name').encode('ascii', 'ignore')
                            mediaXml = get_xml(playonUrl)
                            mediaNode = mediaXml.find('media')
                            src = mediaNode.attrib.get('src')
                            url =  playonInternalUrl + '/' + src
                            vplaylist = xbmc.PlayList( xbmc.PLAYLIST_VIDEO )
                            vplaylist.clear()
                            vplaylist.add(mediaPath + 'DummyEntry.mp4')
                            vplaylist.add(url)
                            listitem=xbmcgui.ListItem (name)
                            xbmc.Player().stop()
                            xbmc.sleep(50)
                            xbmc.Player().play(vplaylist,listitem)
                            xbmc.sleep(50)
                            xbmc.executebuiltin("ActivateWindow('fullscreenvideo')")
        

        

