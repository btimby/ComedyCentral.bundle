BASE_URL = "http://www.cc.com"
SHOW_EXCLUSIONS = ["The Daily Show With Jon Stewart", "The Colbert Report", "South Park", "The Daily Show"]
SHOW_FEED = 'http://www.cc.com/feeds/ent_m081_cc/1.0/4043f1d9-d18f-48a3-89e0-68acad5236f1'
EPISODE_FEED = ['http://www.cc.com/feeds/f1010/1.0/5a123a71-d8b9-45d9-85d5-e85508b1b37c/%s/1', 'http://www.cc.com/feeds/ent_m010_cc/b/1.0/%s']
STANDUP_FEED = 'http://www.cc.com/feeds/ent_m080_cc/1.0/ee4047bd-e5aa-474c-aa62-e7415535e276'
SAMPLE_FEED = 'http://www.cc.com/feeds/ent_m080_cc/1.0/1159cd2a-34d8-42ed-8db6-c479c5c6ba65'

####################################################################################################
def Start():

    ObjectContainer.title1 = "Comedy Central"
    HTTP.CacheTime = CACHE_1HOUR
    HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.125 Safari/537.36'

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

        show_title = shows['show']['title']

        if show_title in SHOW_EXCLUSIONS:
            continue

        show_id = shows['show']['id']
        show_desc = shows['show']['shortDescription'].replace('ABOUT THE SERIES: ', '')

        # There are 3 to 6 images available. This allows us to look for a larger image or at least one that is a proper icon size
        show_img_hgt = 0
        show_img_total = len(shows['show']['images'])
        x = 0

        while show_img_hgt < 400 and x < show_img_total:
            show_img_hgt = shows['show']['images'][x]['height']
            show_img = shows['show']['images'][x]['url']
            x = x+1

        oc.add(DirectoryObject(
            key = Callback(VideoFeed, show_id=show_id, title=show_title),
            title = show_title,
            summary = show_desc,
            thumb = Resource.ContentsOfURLWithFallback(url=show_img)
        ))

    return oc

####################################################################################################
@route("/video/comedycentral/videofeed")
def VideoFeed(title, show_id='', show_url=''):

    oc = ObjectContainer(title2=title)
    feed_urls = []
    episode_ids = []

    if show_id != '':
        for feed in EPISODE_FEED:
            feed_urls.append(feed % (show_id))

    else:
        feed_urls.append(show_url)

    for url in feed_urls:

        json = JSON.ObjectFromURL(url)

        for video in json['result']['episodes']:

            vid_id = video['id']

            if vid_id in episode_ids:
                continue

            episode_ids.append(vid_id)

            vid_url = video['url']
            vid_name = video['title']
            vid_desc = video['description']
            vid_date = int(video['airDate'])
            vid_date = Datetime.FromTimestamp(vid_date)
            vid_duration = Datetime.MillisecondsFromString(video['duration'])
            episode = video['season']['episodeNumber']
            season = video['season']['seasonNumber']
            vid_img = video['images'][0]['url']

            oc.add(EpisodeObject(
                url = vid_url,
                title = vid_name,
                summary = vid_desc,
                originally_available_at = vid_date,
                duration = vid_duration,
                season = int(season),
                index = int(episode),
                thumb = Resource.ContentsOfURLWithFallback(url=vid_img)
            ))

    if len(oc) < 1:
        return ObjectContainer(header="Error", message="This category does not contain any video.")
    else:
        oc.objects.sort(key=lambda obj: obj.originally_available_at, reverse=True)
        return oc
