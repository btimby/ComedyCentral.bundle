BASE_URL = "http://www.cc.com"
SHOW_EXCLUSIONS = ["The Daily Show With Jon Stewart", "The Colbert Report", "South Park", "The Daily Show"]

# This json feed pulls the list of shows with full episodes from the CC home page full episode pull down menu at the top
# It includes Broad City, Workaholics, Review, Adam Devine House Party, and Kroll Show which are not picked up by our show feed we use
# but it does not pull Tosh.0 or UCB which have many more episodes. Also it only gives the web page url, so you would need to pull the show id
#NAV_FEED = 'http://www.cc.com/modules/ent_m066_cc/1.1/201ae6af-6825-4f8c-92a4-cf6c58271c88'
# Below is the json feed url for producing all full episodes for a show where %s is the show id
#FEED_JSON_URL = 'http://www.cc.com/feeds/f1010/1.0/5a123a71-d8b9-45d9-85d5-e85508b1b37c/%s/1'
# This Regex will pull the json within the html text of a CC web page
#RE_JSON = Regex("var triforceManifestFeed = (.+?);")

# This json feed pulls the list of shows with full episodes from the CC full episode page "All Shows" pull down menu (about half way down the page)
SHOW_FEED = 'http://www.cc.com/feeds/ent_m081_cc/1.0/4043f1d9-d18f-48a3-89e0-68acad5236f1'
# The json feeds below pulls the carousel sections on the Full Episode page
STANDUP_FEED = 'http://www.cc.com/feeds/ent_m080_cc/1.0/ee4047bd-e5aa-474c-aa62-e7415535e276'
SAMPLE_FEED = 'http://www.cc.com/feeds/ent_m080_cc/1.0/1159cd2a-34d8-42ed-8db6-c479c5c6ba65'
####################################################################################################
def Start():

    ObjectContainer.title1 = "Comedy Central"
    HTTP.CacheTime = CACHE_1HOUR
    HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:18.0) Gecko/20100101 Firefox/18.0'

####################################################################################################
@handler("/video/comedycentral", "Comedy Central")
def MainMenu():

    oc = ObjectContainer()
    oc.add(DirectoryObject(key = Callback(Shows, title="Shows"), title = "Shows"))
    oc.add(DirectoryObject(key = Callback(VideoFeed, title="Standup Specials", show_url=STANDUP_FEED), title = "Standup Specials"))
    oc.add(DirectoryObject(key = Callback(VideoFeed, title="Free Samples", show_url=SAMPLE_FEED), title = "Free Samples"))
    return oc

####################################################################################################
# This builds a directory of shows from the Full Episode page "all Shows" pull down about half way down the page
@route("/video/comedycentral/shows")
def Shows(title):

    oc = ObjectContainer(title2=title)

    json = JSON.ObjectFromURL(SHOW_FEED, cacheTime = CACHE_1DAY)
    for shows in json['result']['shows']:
        show_url = shows['fullEpisodesFeedURL']
        show_title = shows['show']['title']
        Log('the value of show_title is %s' %show_title)
        if show_title in SHOW_EXCLUSIONS:
            continue
        show_desc = shows['show']['shortDescription'].replace('ABOUT THE SERIES: ', '')
        show_img_hgt = 0
        show_img_total = len(shows['show']['images'])
        x=0
        # There are 3 to 6 images available. This allows us to look for a larger image or at least one that is a proper icon size
        while show_img_hgt < 400 and x<show_img_total:
            show_img_hgt = shows['show']['images'][x]['height']
            show_img = shows['show']['images'][x]['url']
            x=x+1
        oc.add(DirectoryObject(key = Callback(VideoFeed, show_url=show_url, title=show_title), title = show_title, summary = show_desc, thumb = Resource.ContentsOfURLWithFallback(url=show_img)))
            
    return oc

####################################################################################################
@route("/video/comedycentral/videofeed")
def VideoFeed(title, show_url):

    oc = ObjectContainer(title2=title)

    json = JSON.ObjectFromURL(show_url)
    for video in json['result']['episodes']:
        vid_name = video['title']
        vid_url = video['url']
        vid_duration = Datetime.MillisecondsFromString(video['duration'])
        vid_desc = video['description']
        vid_date = int(video['airDate'])
        vid_date = Datetime.FromTimestamp(vid_date)
        vid_img = video['images'][0]['url']
        episode = video['season']['episodeNumber']
        season = video['season']['seasonNumber']
        Log('the value of season is %s and episode is %s' %(season, episode))
        oc.add(EpisodeObject(
            url = vid_url,
            duration = vid_duration,
            title = vid_name,
            summary = vid_desc,
            originally_available_at = vid_date,
            season = int(season),
            index = int(episode),
            thumb = Resource.ContentsOfURLWithFallback(url=vid_img)
        ))
    if len(oc) < 1:
        return ObjectContainer(header="Error", message="This category does not contain any video.")
    else:
        return oc
