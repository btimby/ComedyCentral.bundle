TITLE = 'Comedy Central'
PREFIX = '/video/comedycentral'

BASE_URL = 'http://www.cc.com'
SHOWS_URL = BASE_URL + '/shows'
TOSH_URL = 'http://tosh.cc.com'
FULL_SPECIALS = BASE_URL + '/shows/stand-up-library'

# Pull the json from the HTML content to prevent any issues with redirects and/or bad urls
RE_MANIFEST = Regex('var triforceManifestFeed = (.+?);', Regex.DOTALL)
EXCLUSIONS = ['South Park']
SEARCH ='http://search.cc.com/solr/cc/select?q=%s&wt=json&start='
ENT_LIST = ['ent_m071', 'f1071', 'ent_m013', 'f1013', 'ent_m081', 'ent_m069', 'ent_m157', 'ent_m020', 'ent_m160', 'ent_m012']

####################################################################################################
def Start():

    ObjectContainer.title1 = TITLE
    HTTP.CacheTime = CACHE_1HOUR
    HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'

####################################################################################################
@handler(PREFIX, TITLE)
def MainMenu():

    oc = ObjectContainer()
    oc.add(DirectoryObject(key = Callback(FeedMenu, title="Full Episodes", url=BASE_URL+'/full-episodes'), title = "Full Episodes"))
    oc.add(DirectoryObject(key = Callback(FeedMenu, title="Shows", url=BASE_URL+'/shows'), title = "Shows"))
    oc.add(DirectoryObject(key = Callback(StandupSections, title="Standup"), title = "Standup"))
    oc.add(InputDirectoryObject(key = Callback(SearchSections, title="Search"), title = "Search"))

    return oc

####################################################################################################
@route(PREFIX + '/standupsections')
def StandupSections(title):
    
    oc = ObjectContainer(title2=title)
    oc.add(DirectoryObject(key = Callback(FeedMenu, title="Comedians", url=BASE_URL+"/comedians"), title = "Comedians"))
    oc.add(DirectoryObject(key = Callback(FeedMenu, title="Videos", url=BASE_URL+"/stand-up/video-clips"), title = "Videos"))
    oc.add(DirectoryObject(key = Callback(FeedMenu, title="Full Specials", url=FULL_SPECIALS), title = "Full Specials"))

    return oc

####################################################################################################
# This function pulls the various json feeds for the video sections of a page 
# including those for an individual show's video and full episodes sections
@route(PREFIX + '/feedmenu')
def FeedMenu(title, url, thumb=''):

    oc = ObjectContainer(title2=title)

    try:
        content = HTTP.Request(url, cacheTime=CACHE_1DAY).content
        zone_list = JSON.ObjectFromString(RE_MANIFEST.search(content).group(1))['manifest']['zones']
    except:
        return ObjectContainer(header="Incompatible", message="Unable to find video feeds for %s." % (url))

    if not thumb:
        try: thumb = HTML.ElementFromString(content).xpath('//meta[@property="og:image"]/@content')[0].strip()
        except: thumb = ''

    for zone in zone_list:

        if zone in ('header', 'footer', 'ads-reporting', 'ENT_M171'):
            continue

        json_feed = zone_list[zone]['feed']

        # Split feed to get ent code
        try: ent_code = json_feed.split('/feeds/')[1].split('/')[0]
        except:
            try: ent_code = json_feed.split('/modules/')[1].split('/')[0]
            except: ent_code = ''

        ent_code = ent_code.split('_cc')[0].split('_tosh')[0]

        if ent_code not in ENT_LIST:
            continue

        result_type = GetType(ent_code)
        json = JSON.ObjectFromURL(json_feed, cacheTime = CACHE_1DAY)

        # Get the title from the promo or playlist area
        try: title = json['result']['playlist']['title']
        except:
            try: title = json['result']['promo']['headline']
            except: title = json['result']['promo']['headerText']

        # Create menu items for those that need to go to Produce Sections
        # ent_m071 and f1071-each show's video clips, ent_m157-comedian lists, and ent_m069- show sections
        if ent_code in ['ent_m071', 'f1071', 'ent_m157'] or (ent_code == 'ent_m069' and url == SHOWS_URL):

            if title not in ['You May Also Like', 'Featured Comedians']:

                oc.add(DirectoryObject(
                    key = Callback(ProduceSection, title=title, url=json_feed, result_type=result_type),
                    title = title,
                    thumb = Resource.ContentsOfURLWithFallback(url=thumb)
               ))

        # Create menu for the others to produce videos
        # ent_m013 and f1013 - each show's full episodes, ent_m020-playlists, ent_m160-Standup video clips, and ent_m012-standup specials listing
        elif ent_code in ['ent_m081','ent_m013', 'f1013', 'ent_m020', 'ent_m160', 'ent_m012']:

            # Checck related items for videos before creating a directory
            if ent_code == 'ent_m012':

                example_url = json['result']['relatedItems'][0]['canonicalURL']

                if ('/video-clips/') not in example_url and ('/full-episodes/') not in example_url:
                    continue

            oc.add(DirectoryObject(
                key = Callback(ShowVideos, title=title, url=json_feed, result_type=result_type),
                title = title,
                thumb = Resource.ContentsOfURLWithFallback(url=thumb)
            ))

        # Also create additional menu items for full episode feeds for each show from Full Episodes URL
        if ent_code == 'ent_m081':

            for item in json['result']['shows']:

                oc.add(DirectoryObject(
                    key = Callback(ShowVideos, title=item['show']['title'], url=item['fullEpisodesFeedURL'], result_type='episodes'),
                    title = item['show']['title'],
                    summary = item['show']['description'],
                    thumb = Resource.ContentsOfURLWithFallback(url=item['show']['images'][0]['url'])
                ))

    if len(oc) < 1:
        return ObjectContainer(header="Empty", message="There are no results to list.")
    else:
        return oc

####################################################################################################
# For Producing the sections from various json feeds
@route(PREFIX + '/producesection')
def ProduceSection(title, url, result_type, thumb=''):

    oc = ObjectContainer(title2=title)
    (section_title, feed_url) = (title, url)
    json = JSON.ObjectFromURL(url)

    item_list = json['result'][result_type]

    if result_type == 'promo':
        item_list = json['result'][result_type]['items']

    for item in item_list:

        # Create a list of show sections
        if result_type == 'shows':

            if item['title'] in EXCLUSIONS:
                continue

            oc.add(DirectoryObject(
                key = Callback(FeedMenu, title=item['title'], url=item['canonicalURL'], thumb=item['images'][0]['url']),
                title = item['title'],
                thumb = Resource.ContentsOfURLWithFallback(url=item['images'][0]['url'])
            ))

        # Create a list of comedian sections
        elif result_type == 'promo':

            oc.add(DirectoryObject(
                key = Callback(FeedMenu, title=item['name'], url=item['canonicalURL'], thumb=item['image']['url']),
                title = item['name'],
                thumb = Resource.ContentsOfURLWithFallback(url=item['image']['url'])
            ))

        # Create a list video sections
        else:
            url = json['result'][result_type][item]

            oc.add(DirectoryObject(
                key = Callback(ShowVideos, title=item, url=url, result_type='videos'),
                title = item,
                thumb = Resource.ContentsOfURLWithFallback(url=thumb)
            ))

    oc.objects.sort(key = lambda obj: obj.title)

    if len(oc) < 1:
        Log ('still no value for objects')
        return ObjectContainer(header="Empty", message="There are no results to list right now.")
    else:
        return oc

####################################################################################################
# This function produces the videos listed in json under items
@route(PREFIX + '/showvideos')
def ShowVideos(title, url, result_type):

    oc = ObjectContainer(title2=title)
    json = JSON.ObjectFromURL(url)

    if 'playlist' in result_type:
        videos = json['result'][result_type]['videos']
    else:
        videos = json['result'][result_type]

    for video in videos:

        vid_url = video['canonicalURL']

        # catch any bad links that get sent here
        if not ('/video-clips/') in vid_url and not ('/full-episodes/') in vid_url:
            continue

        thumb = video['images'][0]['url']

        if result_type == 'relatedItems':

            oc.add(VideoClipObject(
                url = vid_url, 
                title = video['title'], 
                thumb = Resource.ContentsOfURLWithFallback(url=thumb ),
                summary = video['description']
            ))
        else:
            try: episode = int(video['season']['episodeNumber'])
            except: episode = None

            try: season = int(video['season']['seasonNumber'])
            except: season = None

            try: unix_date = video['airDate']
            except:
                try: unix_date = video['publishDate']
                except: unix_date = video['date']['originalPublishDate']['timestamp']
            date = Datetime.FromTimestamp(float(unix_date)).strftime('%m/%d/%Y')
            date = Datetime.ParseDate(date)

            # Durations for clips have decimal points
            duration = video['duration']
            if not isinstance(duration, int):
                duration = int(duration.split('.')[0])
            duration = duration * 1000

            # Everything else has episode and show info now
            oc.add(EpisodeObject(
                url = vid_url, 
                show = video['show']['title'],
                season = season,
                index = episode,
                title = video['title'], 
                thumb = Resource.ContentsOfURLWithFallback(url=thumb ),
                originally_available_at = date,
                duration = duration,
                summary = video['description']
            ))

    try: next_page = json['result']['nextPageURL']
    except: next_page = None

    if next_page and len(oc) > 0:

        oc.add(NextPageObject(
            key = Callback(ShowVideos, title=title, url=next_page, result_type=result_type),
            title = 'Next Page ...'
        ))

    if len(oc) < 1:
        Log ('still no value for objects')
        return ObjectContainer(header="Empty", message="There are no unlocked videos available to watch.")
    else:
        return oc

####################################################################################################
@route(PREFIX + '/searchsections')
def SearchSections(title, query):
    
    oc = ObjectContainer(title2=title)
    json_url = SEARCH % (String.Quote(query, usePlus=False))
    local_url = json_url + '0&defType=edismax'
    json = JSON.ObjectFromURL(local_url)
    search_list = []

    for item in json['response']['docs']:

        if item['bucketName_s'] not in search_list:
            search_list.append(item['bucketName_s'])

    for item in search_list:

        oc.add(DirectoryObject(
            key = Callback(Search, title=item, url=json_url, search_type=item),
            title = item
        ))

    return oc

####################################################################################################
@route(PREFIX + '/search', start=int)
def Search(title, url, start=0, search_type=''):

    oc = ObjectContainer(title2=title)
    local_url = '%s%s&fq=bucketName_s:%s&defType=edismax' % (url, start, search_type)
    json = JSON.ObjectFromURL(local_url)

    for item in json['response']['docs']:

        result_type = item['bucketName_s']
        title = item['title_t']
        full_title = '%s: %s' % (result_type, title)

        try: item_url = item['url_s']
        except: continue

        # For Shows
        if result_type == 'Series':

            oc.add(DirectoryObject(
                key = Callback(FeedMenu, title=item['title_t'], url=item_url, thumb=item['imageUrl_s']),
                title = full_title,
                thumb = Resource.ContentsOfURLWithFallback(url=item['imageUrl_s'])
            ))

        # For Comedians
        elif result_type == 'Comedians':

            oc.add(DirectoryObject(
                key = Callback(FeedMenu, title=item['title_t'], url=item_url, thumb=item['imageUrl_s']),
                title = full_title,
                thumb = Resource.ContentsOfURLWithFallback(url=item['imageUrl_s'])
            ))

        # For Episodes and ShowVideo(video clips)
        else:
            try: season = int(item['seasonNumber_s'].split(':')[0])
            except: season = None

            try: episode = int(item['episodeNumber_s'])
            except: episode = None

            try: show = item['seriesTitle_t']
            except: show = None

            try: summary = item['description_t']
            except: summary = None

            oc.add(EpisodeObject(
                url = item_url, 
                show = show, 
                title = full_title, 
                thumb = Resource.ContentsOfURLWithFallback(url=item['imageUrl_s']),
                summary = summary, 
                season = season, 
                index = episode, 
                duration = Datetime.MillisecondsFromString(item['duration_s']), 
                originally_available_at = Datetime.ParseDate(item['contentDate_dt'])
            ))

    if json['response']['start']+10 < json['response']['numFound']:

        oc.add(NextPageObject(
            key = Callback(Search, title='Search', url=url, search_type=search_type, start=start+10),
            title = 'Next Page ...'
        ))

    if len(oc) < 1:
        return ObjectContainer(header="Empty", message="There are no results to list.")
    else:
        return oc

####################################################################################################
# This function pulls the related type used for pulls by each ENT feed
@route(PREFIX + '/gettype')
def GetType(ent):

    result_type = 'relatedItems'
    ENTTYPE_LIST = [
        {'ent':'ent_m071', 'type':'sortingOptions'},
        {'ent':'f1071', 'type':'sortingOptions'},
        {'ent':'ent_m013', 'type':'episodes'},
        {'ent':'f1013', 'type':'episodes'},
        {'ent':'ent_m081', 'type':'episodes'},
        {'ent':'ent_m069', 'type':'shows'},
        {'ent':'ent_m157', 'type':'promo'},
        {'ent':'ent_m020', 'type':'playlist'},
        {'ent':'ent_m160', 'type':'items'}
    ]

    for item in ENTTYPE_LIST:

        if ent == item['ent']:
            result_type = item['type']
            break

    return result_type
