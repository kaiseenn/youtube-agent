#!/usr/bin/env python3
import requests
import json
import sys
import re
from google.adk.tools import FunctionTool

# ======================================================================================================================
# CORE FUNCTIONS
# ======================================================================================================================

def extract_video_id(youtube_url):
    """
    Extract video ID from various YouTube URL formats.
    """
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com/watch\?.*v=([a-zA-Z0-9_-]{11})',
        r'youtu\.be/([a-zA-Z0-9_-]{11})',
        r'youtube\.com/embed/([a-zA-Z0-9_-]{11})'
    ]
    for pattern in patterns:
        match = re.search(pattern, youtube_url)
        if match:
            return match.group(1)
    raise ValueError(f"Could not extract video ID from URL: {youtube_url}")

def parse_vote_count(vote_text):
    """
    Parses vote count text (e.g., "1.2K", "1,234") into an integer.
    Returns 0 if parsing fails or text is not a valid number format.
    """
    if not isinstance(vote_text, str):
        return 0
    
    vote_text = vote_text.strip().lower()
    if not vote_text:
        return 0

    num_part = vote_text.split(' ')[0]
    num_part = num_part.replace(',', '')
    
    multiplier = 1
    if num_part.endswith('k'):
        multiplier = 1000
        num_part = num_part[:-1]
    elif num_part.endswith('m'):
        multiplier = 1000000
        num_part = num_part[:-1]
    elif num_part.endswith('b'):
        multiplier = 1000000000
        num_part = num_part[:-1]
        
    try:
        return int(float(num_part) * multiplier)
    except ValueError:
        return 0

def get_video_page(video_id):
    """
    Fetches the HTML content of a YouTube video page.
    """
    url = f"https://www.youtube.com/watch?v={video_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "en-US,en;q=0.9",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Dest": "document",
    }
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.text
        else:
            print(f"Error: HTTP {response.status_code}", file=sys.stderr)
            return None
    except Exception as e:
        print(f"Request failed: {str(e)}", file=sys.stderr)
        return None

def extract_ytInitialData(html_content):
    """
    Parses the ytInitialData JSON from the video page's HTML.
    """
    match = re.search(r'var ytInitialData = (\{.*?\});', html_content)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError as e:
            print(f"Error decoding ytInitialData JSON: {e}", file=sys.stderr)
            return None
    return None

def extract_comment_token(ytInitialData, newest=False):
    """
    Extracts the continuation token for comments from ytInitialData.
    """
    try:
        engagement_panels = ytInitialData['engagementPanels']
        comments_panel_renderer = None
        for panel in engagement_panels:
            if panel.get('engagementPanelSectionListRenderer', {}).get('panelIdentifier') == 'engagement-panel-comments-section':
                comments_panel_renderer = panel['engagementPanelSectionListRenderer']
                break
        
        if not comments_panel_renderer:
            print("Could not find comments section renderer.", file=sys.stderr)
            return None

        sort_menu = comments_panel_renderer['header']['engagementPanelTitleHeaderRenderer']['menu']['sortFilterSubMenuRenderer']['subMenuItems']
        target_title = "Newest first" if newest else "Top comments"
        
        token_endpoint = next(item for item in sort_menu if item['title'] == target_title)
        
        return token_endpoint['serviceEndpoint']['continuationCommand']['token']
    except (KeyError, StopIteration, TypeError, IndexError) as e:
        print(f"Error extracting comment token: {e}", file=sys.stderr)
        return None

def fetch_comments(continuation_token):
    """
    Fetches comments using the continuation token.
    """
    url = "https://www.youtube.com/youtubei/v1/next?prettyPrint=false"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "X-Youtube-Client-Name": "1",
        "X-Youtube-Client-Version": "2.20250710.09.00",
        "X-Youtube-Bootstrap-Logged-In": "false",
        "Origin": "https://www.youtube.com",
        "Referer": "https://www.youtube.com/",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "same-origin",
        "Sec-Fetch-Dest": "empty",
    }
    context = {
        "client": {
            "hl": "en", "gl": "CA", "remoteHost": "149.88.98.167", "deviceMake": "", "deviceModel": "",
            "visitorData": "CgtuMGtDeGI1N1AyTSjludXDBjIKCgJDQRIEGgAgQw%3D%3D",
            "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36,gzip(gfe)",
            "clientName": "WEB", "clientVersion": "2.20250710.09.00", "osName": "Windows", "osVersion": "10.0",
            "platform": "DESKTOP", "clientFormFactor": "UNKNOWN_FORM_FACTOR",
            "userInterfaceTheme": "USER_INTERFACE_THEME_LIGHT", "timeZone": "America/Toronto",
            "browserName": "Chrome", "browserVersion": "138.0.0.0",
        },
        "user": {"lockedSafetyMode": False},
        "request": {"useSsl": True, "consistencyTokenJars": [], "internalExperimentFlags": []}
    }
    payload = {"context": context, "continuation": continuation_token}

    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error fetching comments: HTTP {response.status_code}\n{response.text}", file=sys.stderr)
            return None
    except Exception as e:
        print(f"Error fetching comments: {e}", file=sys.stderr)
        return None

def extract_comments(comments_data, is_initial=False):
    """
    Extracts comment details from the comments data.
    """
    comments = []
    try:
        # The comment data can be in different places depending on the response
        
        # Try finding comments in reload/append actions
        endpoints = comments_data.get('onResponseReceivedEndpoints', [])
        for endpoint in endpoints:
            action = endpoint.get('reloadContinuationItemsCommand') or endpoint.get('appendContinuationItemsAction')
            if action:
                for item in action.get('continuationItems', []):
                    if 'commentThreadRenderer' in item:
                        comment_renderer = item['commentThreadRenderer'].get('comment', {}).get('commentRenderer', {})
                        if comment_renderer:
                            text = ''.join(run['text'] for run in comment_renderer.get('contentText', {}).get('runs', []))
                            votes = comment_renderer.get('voteCount', {}).get('simpleText', '0')
                            published_time = comment_renderer.get('publishedTimeText', {}).get('runs', [{}])[0].get('text')
                            comments.append({"text": text, "votes": votes, "published_time": published_time})

        # Try finding comments in framework updates (for initial load)
        if 'frameworkUpdates' in comments_data and not comments:
            mutations = comments_data.get('frameworkUpdates', {}).get('entityBatchUpdate', {}).get('mutations', [])
            for mutation in mutations:
                payload = mutation.get('payload', {})
                if 'commentEntityPayload' in payload:
                    comment_payload = payload['commentEntityPayload']
                    content = comment_payload.get('properties', {}).get('content', {}).get('content')
                    votes = comment_payload.get('toolbar', {}).get('likeCountNotliked', '0')
                    published_time = comment_payload.get('properties', {}).get('publishedTime')
                    if content:
                        comments.append({"text": content, "votes": votes, "published_time": published_time})

    except (KeyError, IndexError, TypeError) as e:
        print(f"Error extracting comments: {e}", file=sys.stderr)
    
    if not comments and not is_initial:
         print(f"Could not extract comments from response.", file=sys.stderr)

    return comments

def extract_next_continuation_token(comments_data):
    """
    Extracts the next continuation token from a comments response.
    """
    try:
        endpoints = comments_data.get('onResponseReceivedEndpoints', [])
        if not endpoints:
            return None

        for endpoint in endpoints:
            action = endpoint.get('reloadContinuationItemsCommand') or endpoint.get('appendContinuationItemsAction')
            
            if action:
                continuation_items = action.get('continuationItems')

                if continuation_items:
                    for item in continuation_items:
                        if 'continuationItemRenderer' in item:
                            continuation_endpoint = item['continuationItemRenderer'].get('continuationEndpoint')
                            if continuation_endpoint and 'continuationCommand' in continuation_endpoint:
                                return continuation_endpoint['continuationCommand']['token']

    except (KeyError, IndexError, TypeError) as e:
        print(f"Error extracting next continuation token: {e}", file=sys.stderr)
    return None

def get_comments(video_id: str, max_results: int = 20, sort_by_newest: bool = False) -> list:
    """
    Retrieves comments from a YouTube video ID.

    This function orchestrates the process of fetching comments by first extracting
    the video ID from the URL, then acquiring an initial continuation token, and
    finally fetching comments in a loop until the desired number of results is
    reached.

    Args:
        video_id (str): The unique identifier of the YouTube video.
        max_results (int): The maximum number of comments to retrieve. Defaults to 20.
        sort_by_newest (bool): If True, fetches the newest comments first. If False,
                               fetches the top-voted comments. Defaults to False.

    Returns:
        list: A list of dictionaries, where each dictionary represents a comment
              and contains the following keys:
              - 'text' (str): The content of the comment.
              - 'votes' (str): A string representing the number of votes
                               (e.g., "1.2K", "25").
              - 'published_time' (str): A human-readable string indicating when
                                      the comment was published (e.g., "3 days ago").
              The list is sorted by the number of votes in descending order.
    
    Raises:
        Exception: If the initial video page or subsequent comment data fails to load.
    """
    html_content = get_video_page(video_id)
    if not html_content:
        raise Exception("Failed to retrieve video page.")
        
    ytInitialData = extract_ytInitialData(html_content)
    if not ytInitialData:
        raise Exception("Failed to extract ytInitialData.")
        
    continuation_token = extract_comment_token(ytInitialData, newest=sort_by_newest)

    if continuation_token:
        all_comments = []
        is_initial_fetch = True
        while len(all_comments) < max_results and continuation_token:
            comments_data = fetch_comments(continuation_token)
            if not comments_data:
                break
            
            if is_initial_fetch:
                all_comments.extend(extract_comments(comments_data, is_initial=True))
                is_initial_fetch = False
            else:
                all_comments.extend(extract_comments(comments_data, is_initial=False))

            continuation_token = extract_next_continuation_token(comments_data)

        sorted_comments = sorted(all_comments, key=lambda c: parse_vote_count(c.get('votes', '0')), reverse=True)
        return sorted_comments[:max_results]
    else:
        raise Exception("Failed to extract initial continuation token.")

comments = FunctionTool(func=get_comments)