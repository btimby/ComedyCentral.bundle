BASE_URL = 'http://www.cc.com'
SHOW_EXCLUSIONS = ['the daily show with jon stewart', 'the colbert report', 'south park', 'the daily show']
SHOW_FEED = 'http://www.cc.com/feeds/ent_m069_cc/1.0/5ab40787-7d35-4449-84eb-efadc941cd34'
EPISODE_FEED = ['http://www.cc.com/feeds/ent_m010_cc/b/1.0/%s']
STANDUP_FEED = ['http://www.cc.com/feeds/ent_m080_cc/1.0/ee4047bd-e5aa-474c-aa62-e7415535e276']
SAMPLE_FEED = ['http://www.cc.com/feeds/ent_m080_cc/1.0/1159cd2a-34d8-42ed-8db6-c479c5c6ba65', 'http://www.cc.com/feeds/ent_m079_cc/1.0/dc48e970-132f-49d9-95eb-4a5ae587da16']

####################################################################################################
def Start():

    ObjectContainer.title1 = 'Comedy Central'
    HTTP.CacheTime = CACHE_1HOUR
    HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.125 Safari/537.36'

####################################################################################################
@handler('/video/comedycentral', 'Comedy Central')
def MainMenu():

    oc = ObjectContainer()
    oc.add(DirectoryObject(key = Callback(Shows, title="Shows"), title = "Shows"))
    oc.add(DirectoryObject(key = Callback(VideoFeed, title="Standup Specials"), title = "Standup Specials"))
    oc.add(DirectoryObject(key = Callback(VideoFeed, title="Free Samples"), title = "Free Samples"))
    return oc

####################################################################################################
# This builds a directory of shows from the Full Episode page "all Shows" pull down about half way down the page
@route('/video/comedycentral/shows')
def Shows(title):

    oc = ObjectContainer(title2=title)

    json = JSON.ObjectFromURL(SHOW_FEED, cacheTime = CACHE_1DAY)

    for show in json['result']['shows']:

        show_title = show['title']

        if show_title.lower() in SHOW_EXCLUSIONS:
            continue

        show_id = show['id']
        show_desc = show['shortDescription'].replace('ABOUT THE SERIES: ', '')

        # There are 3 to 6 images available. This allows us to look for a larger image or at least one that is a proper icon size
        show_img_hgt = 0
        show_img_total = len(show['images'])
        x = 0

        while show_img_hgt < 400 and x < show_img_total:
            show_img_hgt = show['images'][x]['height']
            show_img = show['images'][x]['url']
            x = x+1

        oc.add(DirectoryObject(
            key = Callback(VideoFeed, show_id=show_id, title=show_title),
            title = show_title,
            summary = show_desc,
            thumb = Resource.ContentsOfURLWithFallback(url=show_img)
        ))

    oc.objects.sort(key=lambda obj: obj.title)
    return oc

####################################################################################################
@route('/video/comedycentral/videofeed')
def VideoFeed(title, show_id=''):

    oc = ObjectContainer(title2=title)
    feed_urls = []
    episode_ids = []

    if show_id != '':
        for feed in EPISODE_FEED:
            feed_urls.append(feed % (show_id))

    elif title == 'Standup Specials':
        feed_urls.extend(STANDUP_FEED)

    elif title == 'Free Samples':
        feed_urls.extend(SAMPLE_FEED)

    for url in feed_urls:

        try:
            json = JSON.ObjectFromURL(url)
        except:
            continue

        if 'nextPageURL' in json['result']:
            feed_urls.append(json['result']['nextPageURL'])

        for video in json['result']['episodes']:

            if not video['show']:
                continue

            show_title = video['show']['title']

            if show_title.lower() in SHOW_EXCLUSIONS:
                continue

            vid_id = video['id']

            if vid_id in episode_ids:
                continue

            episode_ids.append(vid_id)

            vid_url = video['url']
            vid_name = video['title']
            vid_desc = video['description']
            vid_date = int(video['airDate'])
            vid_date = Datetime.FromTimestamp(vid_date)

            try:
                vid_duration = int(video['duration']) * 1000
            except:
                vid_duration = None

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
