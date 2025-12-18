#!/usr/bin/env python3
import requests
import json
import argparse
import sys
import re
from typing import Optional

# ======================================================================================================================
# CORE FUNCTIONS
# ======================================================================================================================

def extract_video_id(youtube_url: str) -> str:
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

def parse_vote_count(vote_text: str) -> int:
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

def get_video_page(video_id: str) -> str:
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
            raise ValueError(f"Failed to fetch video page: HTTP {response.status_code}")
    except requests.RequestException as e:
        raise ConnectionError(f"Network error while fetching video page: {str(e)}")

def extract_ytInitialData(html_content: str) -> dict:
    match = re.search(r'var ytInitialData = (\{.*?\});', html_content)
    if not match:
        raise ValueError("Could not find ytInitialData in page HTML")
    
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse ytInitialData JSON: {str(e)}")

def extract_comment_token(ytInitialData: dict, newest: bool = False) -> Optional[str]:
    try:
        engagement_panels = ytInitialData.get('engagementPanels')
        if not engagement_panels:
            return None
            
        comments_panel_renderer = None
        for panel in engagement_panels:
            if panel.get('engagementPanelSectionListRenderer', {}).get('panelIdentifier') == 'engagement-panel-comments-section':
                comments_panel_renderer = panel['engagementPanelSectionListRenderer']
                break
        
        if not comments_panel_renderer:
            return None

        sort_menu = comments_panel_renderer['header']['engagementPanelTitleHeaderRenderer']['menu']['sortFilterSubMenuRenderer']['subMenuItems']
        target_title = "Newest first" if newest else "Top comments"
        
        token_endpoint = next(item for item in sort_menu if item['title'] == target_title)
        
        return token_endpoint['serviceEndpoint']['continuationCommand']['token']
    except (KeyError, StopIteration, TypeError, IndexError) as e:
        raise ValueError(f"Failed to extract comment token due to unexpected page structure: {str(e)}")

def fetch_comments(continuation_token: str) -> dict:
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
            raise ValueError(f"Failed to fetch comments: HTTP {response.status_code}")
    except requests.RequestException as e:
        raise ConnectionError(f"Network error while fetching comments: {str(e)}")

def extract_comments(comments_data: dict, is_initial: bool = False) -> list[dict]:
    comments = []
    try:
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
        pass

    return comments

def extract_next_continuation_token(comments_data: dict) -> Optional[str]:
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
        pass
    return None

# ======================================================================================================================
# HIGH-LEVEL FUNCTION FOR EXTERNAL USE
# ======================================================================================================================

def get_comments(video_url_or_id: str, max_comments: int = 20, sort_by_newest: bool = False) -> Optional[list[dict]]:
    if 'youtube.com' in video_url_or_id or 'youtu.be' in video_url_or_id:
        video_id = extract_video_id(video_url_or_id)
    else:
        video_id = video_url_or_id
    
    try:
        html_content = get_video_page(video_id)
        ytInitialData = extract_ytInitialData(html_content)
        continuation_token = extract_comment_token(ytInitialData, newest=sort_by_newest)
        if not continuation_token:
            return None
        
        all_comments = []
        is_initial_fetch = True
        
        while len(all_comments) < max_comments and continuation_token:
            comments_data = fetch_comments(continuation_token)
            
            all_comments.extend(extract_comments(comments_data, is_initial=is_initial_fetch))
            continuation_token = extract_next_continuation_token(comments_data)
            is_initial_fetch = False
        
        sorted_comments = sorted(all_comments, key=lambda c: parse_vote_count(c.get('votes', '0')), reverse=True)
        return sorted_comments[:max_comments]
    except (ValueError, ConnectionError):
        raise
    except Exception as e:
        raise RuntimeError(f"Unexpected error while fetching comments: {str(e)}")
