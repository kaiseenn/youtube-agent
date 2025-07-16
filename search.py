import requests
import json
import argparse

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
        payload = {"context": context, "query": query, "params": "CAM%3D"}

    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code != 200:
            print(f"Error: HTTP {response.status_code}\nResponse: {response.text}")
            return None
        return response.json()
    except Exception as e:
        print(f"Request failed: {str(e)}")
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
            print("Could not find video content in the response.")
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
            view_count = renderer.get('viewCountText', {}).get('simpleText')

            if video_id and title:
                videos.append({"title": title, "view_count": view_count, "video_id": video_id})
    return videos

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
    """Prints formatted video information."""
    print("--- Extracted Video Information ---")
    print("Title, View Count, Video ID")
    print("---------------------------------")
    for video in videos:
        print(f'"{video["title"]}", "{video.get("view_count", "N/A")}", "{video["video_id"]}"')

def parse_filter_renderers(response_data):
    """
    Parses searchFilterRenderer objects from the YouTube search response.
    """
    try:
        print("\n--- Extracted Filter Information ---")
        groups = response_data['header']['searchHeaderRenderer']['searchFilterButton']['buttonRenderer']['command']['openPopupAction']['popup']['searchFilterOptionsDialogRenderer']['groups']
        for group in groups:
            group_renderer = group.get('searchFilterGroupRenderer', {})
            title = group_renderer.get('title', {}).get('simpleText')
            if title:
                print(f"\n{title}:")
            
            for f in group_renderer.get('filters', []):
                renderer = f.get('searchFilterRenderer', {})
                tooltip = renderer.get('tooltip')
                params = renderer.get('navigationEndpoint', {}).get('searchEndpoint', {}).get('params')
                if tooltip:
                    status = "(selected)" if renderer.get('status') == 'FILTER_STATUS_SELECTED' else params
                    print(f"  {tooltip}: {status}")

    except (KeyError, IndexError, TypeError) as e:
        print(f"An error occurred while parsing filter renderers: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Search YouTube videos')
    parser.add_argument('query', help='Search query')
    parser.add_argument('--exclude-shorts', action='store_true', help='Exclude YouTube Shorts from the results')
    parser.add_argument('--results', type=int, default=10, help='Number of results to fetch')
    args = parser.parse_args()
    
    print(f"Searching YouTube for: '{args.query}' | Aiming for {args.results} results.\n")
    
    all_videos = []
    response_data = search_youtube_videos(args.query)

    if response_data:
        try:
            with open('response.txt', 'w', encoding='utf-8') as f:
                json.dump(response_data, f, indent=2, ensure_ascii=False)
            print("Full response from initial search saved to response.txt\n")
        except Exception as e:
            print(f"Failed to save response to file: {e}")

        all_videos.extend(extract_videos(response_data, args.exclude_shorts))
        continuation_token = extract_continuation_token(response_data)
        
        parse_filter_renderers(response_data)

        while len(all_videos) < args.results and continuation_token:
            print(f"\nCollected {len(all_videos)} videos, fetching more...")
            response_data = search_youtube_videos(args.query, continuation=continuation_token)
            if not response_data:
                break
            
            all_videos.extend(extract_videos(response_data, args.exclude_shorts))
            continuation_token = extract_continuation_token(response_data)

        print_videos_info(all_videos[:args.results])
    else:
        print("Failed to get search results")
        exit(1)
    
    exit(0) 