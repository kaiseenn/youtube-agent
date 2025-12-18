import requests
import json
import argparse
import sys
from typing import Optional
from urllib.parse import quote_plus

def search_youtube_videos(query: str, continuation: Optional[str] = None) -> requests.Response:
    url = "https://www.youtube.com/youtubei/v1/search?prettyPrint=false"
    safe_query = quote_plus(query) if query else ''
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
        "Referer": f"https://www.youtube.com/results?search_query={safe_query}",
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
            "originalUrl": f"https://www.youtube.com/results?search_query={safe_query}",
            "platform": "DESKTOP", "clientFormFactor": "UNKNOWN_FORM_FACTOR",
            "userInterfaceTheme": "USER_INTERFACE_THEME_LIGHT", "timeZone": "America/Toronto",
            "browserName": "Chrome", "browserVersion": "138.0.0.0",
            "acceptHeader": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "screenWidthPoints": 1247, "screenHeightPoints": 1277, "screenPixelDensity": 1, "screenDensityFloat": 1,
            "utcOffsetMinutes": -240, "memoryTotalKbytes": "8000000",
            "mainAppWebInfo": {
                "graftUrl": f"/results?search_query={safe_query}",
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
        payload = {"context": context, "query": query, "params": "CAM%3D", "webSearchboxStatsUrl": f"/search?oq={safe_query}&gs_l=youtube.12.....0.6277......0......................"}

    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code != 200:
            raise ValueError(f"YouTube search API returned status code {response.status_code}")
        return response
    except requests.RequestException as e:
        raise ConnectionError(f"Network error while searching YouTube: {str(e)}")

def parse_view_count(vc_text: str) -> Optional[int]:
    if not vc_text:
        return None
    
    if vc_text.lower().startswith("no"):
        return 0
    
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

def extract_videos(response_data: dict, exclude_shorts: bool = False) -> list[dict]:
    videos = []
    try:
        contents = response_data['onResponseReceivedCommands'][0]['appendContinuationItemsAction']['continuationItems']
    except (KeyError, IndexError):
        try:
            contents = response_data['contents']['twoColumnSearchResultsRenderer']['primaryContents']['sectionListRenderer']['contents']
        except (KeyError, IndexError):
            return videos

    video_contents = []
    for item in contents:
        if 'itemSectionRenderer' in item:
            video_contents.extend(item['itemSectionRenderer']['contents'])
        elif 'continuationItemRenderer' in item:
            pass

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
                    pass

            if video_id and title:
                videos.append({"title": title, "channel_name": channel_name, "view_count": view_count, "video_id": video_id, "published_time": published_time_text, "description_snippet": description_snippet})
    return videos

def extract_continuation_token(response_data: dict) -> Optional[str]:
    try:
        contents = response_data['contents']['twoColumnSearchResultsRenderer']['primaryContents']['sectionListRenderer']['contents']
    except KeyError:
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

def parse_filter_renderers(response_data: dict) -> Optional[list[dict]]:
    try:
        groups = response_data['header']['searchHeaderRenderer']['searchFilterButton']['buttonRenderer']['command']['openPopupAction']['popup']['searchFilterOptionsDialogRenderer']['groups']
        filters_info = []
        for group in groups:
            group_renderer = group.get('searchFilterGroupRenderer', {})
            title = group_renderer.get('title', {}).get('simpleText')
            
            for f in group_renderer.get('filters', []):
                renderer = f.get('searchFilterRenderer', {})
                tooltip = renderer.get('tooltip')
                params = renderer.get('navigationEndpoint', {}).get('searchEndpoint', {}).get('params')
                if tooltip:
                    status = "(selected)" if renderer.get('status') == 'FILTER_STATUS_SELECTED' else params
                    filters_info.append({"title": title, "tooltip": tooltip, "status": status})
        return filters_info
    except (KeyError, IndexError, TypeError) as e:
        return None

# ======================================================================================================================
# HIGH-LEVEL FUNCTION FOR EXTERNAL USE
# ======================================================================================================================

def search_videos(query: str, max_results: int = 10, exclude_shorts: bool = False) -> Optional[list[dict]]:
    try:
        all_videos = []
        response = search_youtube_videos(query)
            
        response_data = response.json()
        all_videos.extend(extract_videos(response_data, exclude_shorts))
        continuation_token = extract_continuation_token(response_data)

        while len(all_videos) < max_results and continuation_token:
            response = search_youtube_videos(query, continuation=continuation_token)
            
            response_data = response.json()
            all_videos.extend(extract_videos(response_data, exclude_shorts))
            continuation_token = extract_continuation_token(response_data)

        if len(all_videos) == 0:
            return None
            
        return all_videos[:max_results]
    except (ValueError, ConnectionError):
        raise
    except Exception as e:
        raise RuntimeError(f"Unexpected error while searching videos: {str(e)}")
