import base64
import urllib.parse
import requests
import json
import argparse
import re

def extract_video_id(youtube_url):
    """
    Extract video ID from various YouTube URL formats
    
    Args:
        youtube_url: YouTube URL in various formats
        
    Returns:
        String containing the video ID
        
    Raises:
        ValueError: If no valid video ID is found
    """
    # Common YouTube URL patterns
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

def generate_youtube_transcript_params(video_id, asr=True):
    """
    Generate YouTube transcript params (English only)
    """
    # Pre-encoded AND URL-encoded inner structures for English
    if asr:
        inner_base64 = 'CgNhc3ISAmVuGgA%3D'  # ASR version with %3D
    else:
        inner_base64 = 'CgASAmVuGgA%3D'      # Manual version with %3D
    
    # Build the params
    params = (
        b'\x0a' + bytes([len(video_id)]) + video_id.encode('ascii') +
        b'\x12' + bytes([len(inner_base64)]) + inner_base64.encode('ascii') +
        b'\x18\x01' +
        b'\x2a\x33engagement-panel-searchable-transcript-search-panel' +
        b'\x30\x01\x38\x01\x40\x01'
    )
    
    return urllib.parse.quote(base64.b64encode(params).decode('ascii'))

def fetch_youtube_transcript_text(video_id, asr=True):
    """
    Fetch YouTube transcript and return only the text
    
    Args:
        video_id: YouTube video ID
        asr: Whether to use ASR (auto-generated) transcripts
        
    Returns:
        String containing all transcript text joined together
    """
    # Generate params
    params = generate_youtube_transcript_params(video_id, asr=asr)
    
    # Build the request payload - conditionally include languageCode
    payload = {
        "context": {
            "client": {
                "hl": "en",
                "gl": "CA",
                "clientName": "WEB",
                "clientVersion": "2.20250710.09.00",
                "osName": "Windows",
                "osVersion": "10.0",
                "platform": "DESKTOP",
                "clientFormFactor": "UNKNOWN_FORM_FACTOR",
                "userInterfaceTheme": "USER_INTERFACE_THEME_LIGHT",
                "browserName": "Chrome",
                "browserVersion": "138.0.0.0",
                "acceptHeader": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36,gzip(gfe)",
                "timeZone": "America/Toronto",
                "utcOffsetMinutes": -240,
                "memoryTotalKbytes": "8000000",
                "mainAppWebInfo": {
                    "graftUrl": f"https://www.youtube.com/watch?v={video_id}",
                    "pwaInstallabilityStatus": "PWA_INSTALLABILITY_STATUS_UNKNOWN",
                    "webDisplayMode": "WEB_DISPLAY_MODE_BROWSER",
                    "isWebNativeShareAvailable": True
                }
            },
            "user": {
                "lockedSafetyMode": False
            },
            "request": {
                "useSsl": True,
                "internalExperimentFlags": [],
                "consistencyTokenJars": []
            }
        },
        "params": params
    }
    
    # Only add languageCode if asr=False (manual transcripts)
    if not asr:
        payload["languageCode"] = "en"
    
    # Headers
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "X-Youtube-Client-Name": "1",
        "X-Youtube-Client-Version": "2.20250710.09.00",
        "X-Youtube-Bootstrap-Logged-In": "false",
        "X-Goog-Visitor-Id": "CgtuMGtDeGI1N1AyTSj2otXDBjIKCgJDQRIEGgAgQw%3D%3D",
        "Origin": "https://www.youtube.com",
        "Referer": f"https://www.youtube.com/watch?v={video_id}",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "same-origin",
        "Sec-Fetch-Dest": "empty"
    }
    
    # Make the request
    url = "https://www.youtube.com/youtubei/v1/get_transcript?prettyPrint=false"
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"Failed to fetch transcript: {response.status_code}")
    
    data = response.json()
    
    # Extract all text from transcript segments
    all_text = []
    
    try:
        # Navigate to the transcript data
        actions = data.get('actions', [])
        for action in actions:
            if 'updateEngagementPanelAction' in action:
                panel = action['updateEngagementPanelAction']['content']['transcriptRenderer']
                body = panel['content']['transcriptSearchPanelRenderer']['body']['transcriptSegmentListRenderer']
                
                # Extract initial segments
                initial_segments = body.get('initialSegments', [])
                for segment in initial_segments:
                    if 'transcriptSegmentRenderer' in segment:
                        seg_data = segment['transcriptSegmentRenderer']
                        # Extract text from all runs
                        text = seg_data['snippet']['runs'][0]['text']
                        all_text.append(text)
                
                break
                
    except (KeyError, IndexError) as e:
        raise Exception(f"Failed to parse transcript data: {str(e)}")
    
    # Join all text with spaces
    return ' '.join(all_text)

# Command Line Interface
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Download YouTube transcript text'
    )
    
    parser.add_argument(
        'url',
        help='YouTube video URL'
    )
    
    args = parser.parse_args()
    
    try:
        # Extract video ID from URL
        video_id = extract_video_id(args.url)
        print(f"Extracting transcript for video ID: {video_id}")
        print(f"Original URL: {args.url}\n")
        
        # Fetch and display transcript
        text = fetch_youtube_transcript_text(video_id)
        print("=== TRANSCRIPT ===")
        print(text)
        exit(0)  # Successful completion
            
    except ValueError as e:
        print(f"URL Error: {str(e)}")
        exit(1)  # Exit with error code for URL issues
    except Exception as e:
        print(f"Error: {str(e)}")
        exit(1)  # Exit with error code for other issues