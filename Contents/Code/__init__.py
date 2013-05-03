BASE_URL = "http://www.comedycentral.com"
MRSS_PATH = "http://www.comedycentral.com/feeds/mrss?uri=%s"
MRSS_NS = {"media": "http://search.yahoo.com/mrss/"}
RE_DURATION = Regex('([0-9]+)')
SHOW_EXCLUSIONS = ["The Daily Show with Jon Stewart", "The Colbert Report", "South Park"]

####################################################################################################
def Start():

	ObjectContainer.title1 = "Comedy Central"
	HTTP.CacheTime = CACHE_1HOUR
	HTTP.Headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:18.0) Gecko/20100101 Firefox/18.0'

####################################################################################################
@handler("/video/comedycentral", "Comedy Central")
def MainMenu():

	oc = ObjectContainer()

	for show in HTML.ElementFromURL("http://www.comedycentral.com/shows").xpath('//ul[@class="shows_list"]/li'):
		name = show.xpath('.//meta[@itemprop="name"]')[0].get('content').encode("utf-8")

		if name in SHOW_EXCLUSIONS:
			continue

		show_url = show.xpath('.//meta[@itemprop="url"]')[0].get('content').encode("utf-8")
		summary = String.StripTags(show.xpath('.//meta[@itemprop="description"]')[0].get('content').replace('Â®', '®'))
		thumb = show.xpath('.//img')[0].get('src').split('?')[0]

		oc.add(DirectoryObject(
			key = Callback(Episodes, show_url=show_url, title=name),
			title = name,
			summary = summary,
			thumb = Resource.ContentsOfURLWithFallback(url=thumb)
		))

	return oc

####################################################################################################
@route("/video/comedycentral/episodes")
def Episodes(show_url, title):

	oc = ObjectContainer(title2=title)

	if not show_url.startswith('http://'):
		show_url = ("http://www.comedycentral.com" + show_url)

	show_page = HTML.ElementFromURL(show_url)
	episodes = show_page.xpath('//div[@class="content"]//div[@itemtype="http://schema.org/TVEpisode"]')
	if len(episodes) > 0:
		Log("Found %s episodes" % len(episodes))
		pass
	else:
		try:
			episodes_url = show_page.xpath('//a[@class="episodes"]')[0].get('href')
		except:
			episodes_url = show_url + 'full-episodes/'
		
		Log("Checking new page for episodes: %s" % episodes_url)
		show_page = HTML.ElementFromURL(episodes_url)
		episodes = show_page.xpath('//div[@class="content"]//div[@itemtype="http://schema.org/TVEpisode"]')

		if len(episodes) < 1:
			''' one last try to grab at least one episode '''
			try:
				HTTP.Request(show_url + 'full-episodes/', follow_redirects=False).headers
			except Ex.RedirectError, e:
				try:
					episode_page = e.location
					oc.add(URLService.MetadataObjectForURL(episode_page))
				except:
					pass

	for episode in episodes:
		url = episode.xpath('.//meta[@itemprop="url"]')[0].get('content')
		title = episode.xpath('.//meta[@itemprop="name"]')[0].get('content')
		thumb = episode.xpath('.//meta[@itemprop="image"]')[0].get('content')
		summary = episode.xpath('.//meta[@itemprop="description"]')[0].get('content')
		date = episode.xpath('.//meta[@itemprop="datePublished"]')[0].get('content')
		if date != "":
			date = Datetime.ParseDate(date).date()
		else:
				date = None
		
		oc.add(VideoClipObject(
			url = url,
			title = title,
			summary = summary,
			originally_available_at = date,
			thumb = Resource.ContentsOfURLWithFallback(url=thumb)
		))

	if len(oc) < 1:
		return ObjectContainer(header="Error", message="This category does not contain any video.")
	else:
		return oc
