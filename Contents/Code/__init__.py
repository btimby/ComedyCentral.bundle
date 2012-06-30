COMCENT_PLUGIN_PREFIX       = "/video/comedycentral"
YAHOO_NAMESPACE  = {'media':'http://search.yahoo.com/mrss/'}

BASE_URL = "http://www.comedycentral.com"
RSS_PATH = "http://www.comedycentral.com/feeds/mrss?uri=%s"

ICON = "icon-default.png"
ART = "art-default.jpg"

SHOW_EXCLUSIONS = ["The Daily Show With Jon Stewart", "The Colbert Report"]
#showurl.count("katz") == 0 and showurl.count("scrubs") == 0 and showurl.count("wanda") == 0 and showurl.count("mad_tv") == 0 and showurl.count("colbert") == 0
####################################################################################################
def Start():
    Plugin.AddPrefixHandler(COMCENT_PLUGIN_PREFIX, MainMenu, "Comedy Central", ICON, ART)
    ObjectContainer.art = R(ART)
    DirectoryObject.thumb = R(ICON)
    ObjectContainer.title1 = "Comedy Central"
####################################################################################################

def MainMenu():
    oc = ObjectContainer()
    for show in HTML.ElementFromURL("http://www.comedycentral.com/shows").xpath('//ul[@class="shows_list"]/li'):
	showurl = show.xpath('.//meta[@itemprop="url"]')[0].get('content').encode("utf-8")
	name = show.xpath('.//meta[@itemprop="name"]')[0].get('content').encode("utf-8")
	summary = show.xpath('.//meta[@itemprop="description"]')[0].get('content')
	thumb = show.xpath('.//img')[0].get('src').split('?')[0]
	if name in SHOW_EXCLUSIONS:
	    continue
	oc.add(DirectoryObject(key=Callback(Level1, showurl=showurl,title=name), title=name, summary=summary,
	    thumb=Resource.ContentsOfURLWithFallback(url=thumb, fallback=ICON)))
    return oc
  
def Level1(showurl, title):
    oc = ObjectContainer(title2=title)
    if not showurl.startswith('http://'):
	showurl = ("http://www.comedycentral.com" + url)

    showpage = HTML.ElementFromURL(showurl)
    id = showpage.xpath('//div[@id="video_player_box"]')[0].get('data-mgid')
    
    rssfeed = RSS.FeedFromURL(RSS_PATH % id)
    for entry in rssfeed.entries:
	title = entry.title
        summary = entry.description
	date = Datetime.ParseDate(entry.updated).date()
	url = entry.links[0]['href']
	thumb = entry.media_thumbnail[0]['url']
	runtime = int(entry.media_content[0]['duration'])*1000
	oc.add(VideoClipObject(url=url, title=title, summary=summary, originally_available_at=date, duration=runtime,
	    thumb=Resource.ContentsOfURLWithFallback(url=thumb, fallback=ICON)))
	
    if len(oc) == 0:
	return ObjectContainer(header="Error", message="This category does not contain any video.")
    else:
	return oc