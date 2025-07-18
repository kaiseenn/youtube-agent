import requests
import json
import sys
from google.adk.tools import FunctionTool

def search_youtube_videos(query, continuation=None):
    """
    Search YouTube videos using the internal API. Can be used for an initial search or for pagination.

    Args:
        query: The search query string for the initial search.
        continuation: The continuation token for fetching subsequent pages.

    Returns:
        The JSON response data from the YouTube API.
    """
    url = "https://www.youtube.com/youtubei/v1/search?prettyPrint=false"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "X-Youtube-Client-Name": "1",
        "X-Youtube-Client-Version": "2.20250710.09.00",
        "X-Youtube-Bootstrap-Logged-In": "false",
        "X-Goog-Visitor-Id": "CgtuMGtDeGI1N1AyTSjludXDBjIKCgJDQRIEGgAgQw%3D%3D",
        "Origin": "https://www.youtube.com",
        "Referer": f"https://www.youtube.com/results?search_query={query.replace(' ', '+') if query else ''}",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "same-origin",
        "Sec-Fetch-Dest": "empty",
        "Sec-Ch-Ua": '"Not)A;Brand";v="8", "Chromium";v="138"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"'
    }

    context = {
        "client": {
            "hl": "en", "gl": "CA", "remoteHost": "149.88.98.167", "deviceMake": "", "deviceModel": "",
            "visitorData": "CgtuMGtDeGI1N1AyTSjludXDBjIKCgJDQRIEGgAgQw%3D%3D",
            "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36,gzip(gfe)",
            "clientName": "WEB", "clientVersion": "2.20250710.09.00", "osName": "Windows", "osVersion": "10.0",
            "originalUrl": f"https://www.youtube.com/results?search_query={query.replace(' ', '+') if query else ''}",
            "platform": "DESKTOP", "clientFormFactor": "UNKNOWN_FORM_FACTOR",
            "userInterfaceTheme": "USER_INTERFACE_THEME_LIGHT", "timeZone": "America/Toronto",
            "browserName": "Chrome", "browserVersion": "138.0.0.0",
            "acceptHeader": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "screenWidthPoints": 1247, "screenHeightPoints": 1277, "screenPixelDensity": 1, "screenDensityFloat": 1,
            "utcOffsetMinutes": -240, "memoryTotalKbytes": "8000000",
            "mainAppWebInfo": {
                "graftUrl": f"/results?search_query={query.replace(' ', '+') if query else ''}",
                "pwaInstallabilityStatus": "PWA_INSTALLABILITY_STATUS_UNKNOWN",
                "webDisplayMode": "WEB_DISPLAY_MODE_BROWSER",
                "isWebNativeShareAvailable": True
            }
        },
        "user": {"lockedSafetyMode": False},
        "request": {"useSsl": True, "consistencyTokenJars": [], "internalExperimentFlags": []}
    }

    if continuation:
        payload = {"context": context, "continuation": continuation}
    else:
        payload = {"context": context, "query": query, "params": "CAM%3D", "webSearchboxStatsUrl": f"/search?oq={query.replace(' ', '+') if query else ''}&gs_l=youtube.12.....0.6277......0......................"}

    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code != 200:
            print(f"Error: HTTP {response.status_code}\nResponse: {response.text}", file=sys.stderr)
            return None
        return response.json()
    except Exception as e:
        print(f"Request failed: {str(e)}", file=sys.stderr)
        return None

def parse_view_count(vc_text):
    """
    Parses view count text (e.g., "1.2M views", "1,234 views", "No views") into an integer.
    """
    if not vc_text:
        return None
    
    # "No views" case
    if vc_text.lower().startswith("no"):
        return 0
    
    # Take first part which should be the number
    num_part = vc_text.split(' ')[0]
    num_part = num_part.replace(',', '')
    
    multiplier = 1
    if num_part.lower().endswith('k'):
        multiplier = 1000
        num_part = num_part[:-1]
    elif num_part.lower().endswith('m'):
        multiplier = 1_000_000
        num_part = num_part[:-1]
    elif num_part.lower().endswith('b'):
        multiplier = 1_000_000_000
        num_part = num_part[:-1]
        
    try:
        return int(float(num_part) * multiplier)
    except ValueError:
        return None

def extract_videos(response_data, exclude_shorts=False):
    """
    Extracts video details from a YouTube search response.
    """
    videos = []
    try:
        contents = response_data['onResponseReceivedCommands'][0]['appendContinuationItemsAction']['continuationItems']
    except (KeyError, IndexError):
        try:
            contents = response_data['contents']['twoColumnSearchResultsRenderer']['primaryContents']['sectionListRenderer']['contents']
        except (KeyError, IndexError):
            print("Could not find video content in the response.", file=sys.stderr)
            return videos

    video_contents = []
    for item in contents:
        if 'itemSectionRenderer' in item:
            video_contents.extend(item['itemSectionRenderer']['contents'])
        elif 'continuationItemRenderer' in item:
            pass  # This is handled by extract_continuation_token

    for item in video_contents:
        if 'videoRenderer' in item:
            renderer = item['videoRenderer']
            if exclude_shorts:
                nav_endpoint = renderer.get('navigationEndpoint', {})
                command_metadata = nav_endpoint.get('commandMetadata', {})
                web_command_metadata = command_metadata.get('webCommandMetadata', {})
                url = web_command_metadata.get('url')

                if url and url.startswith('/shorts'):
                    continue
            
            video_id = renderer.get('videoId')
            title = renderer.get('title', {}).get('runs', [{}])[0].get('text')
            view_count_text = renderer.get('viewCountText', {}).get('simpleText')
            view_count = parse_view_count(view_count_text)
            published_time_text = renderer.get('publishedTimeText', {}).get('simpleText')
            try:
                channel_name = renderer['ownerText']['runs'][0]['text']
            except (KeyError, IndexError):
                channel_name = None

            description_snippet = None
            if 'detailedMetadataSnippets' in renderer:
                try:
                    snippet_runs = renderer['detailedMetadataSnippets'][0]['snippetText']['runs']
                    description_snippet = "".join(run.get('text', '') for run in snippet_runs)
                except (KeyError, IndexError, TypeError):
                    pass  # Keep it None if parsing fails

            if video_id and title:
                videos.append({"title": title, "channel_name": channel_name, "view_count": view_count, "video_id": video_id, "published_time": published_time_text, "description_snippet": description_snippet})
    return videos

def search_youtube(query: str, max_results: int = 10, exclude_shorts: bool = False) -> list:
    """
    Performs a YouTube search and returns a list of video results.

    This function queries YouTube's internal API to find videos matching the
    specified query. It supports pagination to fetch a desired number of results
    and can optionally filter out YouTube Shorts.

    Args:
        query (str): The search term to look for on YouTube.
        max_results (int): The maximum number of video results to return.
                           Defaults to 10.
        exclude_shorts (bool): If True, YouTube Shorts will be omitted from the
                               search results. Defaults to False.

    Returns:
        list: A list of dictionaries, where each dictionary represents a video
              and contains the following keys:
              - 'title' (str): The title of the video.
              - 'channel_name' (str): The name of the channel that uploaded the video.
              - 'view_count' (int): The number of views the video has.
              - 'video_id' (str): The unique identifier for the video.
              - 'published_time' (str): A human-readable string indicating when
                                      the video was published (e.g., "2 weeks ago").
              - 'description_snippet' (str): A short snippet from the video's description.
    """
    all_videos = []
    response_data = search_youtube_videos(query)

    if response_data:
        all_videos.extend(extract_videos(response_data, exclude_shorts))
        continuation_token = extract_continuation_token(response_data)

        while len(all_videos) < max_results and continuation_token:
            response_data = search_youtube_videos(query, continuation=continuation_token)
            if not response_data:
                break
            
            all_videos.extend(extract_videos(response_data, exclude_shorts))
            continuation_token = extract_continuation_token(response_data)
    
    return all_videos[:max_results]


def extract_continuation_token(response_data):
    """
    Extracts the continuation token from a YouTube search response.
    """
    try:
        # For initial response
        contents = response_data['contents']['twoColumnSearchResultsRenderer']['primaryContents']['sectionListRenderer']['contents']
    except KeyError:
        # For continuation responses
        try:
            contents = response_data['onResponseReceivedCommands'][0]['appendContinuationItemsAction']['continuationItems']
        except (KeyError, IndexError):
            return None

    for item in contents:
        if 'continuationItemRenderer' in item:
            try:
                return item['continuationItemRenderer']['continuationEndpoint']['continuationCommand']['token']
            except KeyError:
                continue
    return None

def print_videos_info(videos):
    """Prints formatted video information as a JSON array."""
    print(json.dumps(videos, indent=2, ensure_ascii=False))

def parse_filter_renderers(response_data):
    """
    Parses searchFilterRenderer objects from the YouTube search response.
    """
    try:
        print("\n--- Extracted Filter Information ---", file=sys.stderr)
        groups = response_data['header']['searchHeaderRenderer']['searchFilterButton']['buttonRenderer']['command']['openPopupAction']['popup']['searchFilterOptionsDialogRenderer']['groups']
        for group in groups:
            group_renderer = group.get('searchFilterGroupRenderer', {})
            title = group_renderer.get('title', {}).get('simpleText')
            if title:
                print(f"\n{title}:", file=sys.stderr)
            
            for f in group_renderer.get('filters', []):
                renderer = f.get('searchFilterRenderer', {})
                tooltip = renderer.get('tooltip')
                params = renderer.get('navigationEndpoint', {}).get('searchEndpoint', {}).get('params')
                if tooltip:
                    status = "(selected)" if renderer.get('status') == 'FILTER_STATUS_SELECTED' else params
                    print(f"  {tooltip}: {status}", file=sys.stderr)

    except (KeyError, IndexError, TypeError) as e:
        print(f"An error occurred while parsing filter renderers: {e}", file=sys.stderr) 


search = FunctionTool(func=search_youtube)