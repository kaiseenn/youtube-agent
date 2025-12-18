import base64
import urllib.parse
import requests
import argparse
import re
import psycopg2
import os
import json
from typing import Optional

def get_db_connection() -> Optional[psycopg2.extensions.connection]:
    try:
        conn = psycopg2.connect(
            dbname = os.getenv("dbname","searchagent"),
            user = os.getenv("user"),
            password = os.getenv("password"),
            host = os.getenv("host", "localhost"),
            port = os.getenv("port", "5432")
        )
        return conn
    except psycopg2.Error as e:
        print(f"Database connection error: {e}")
        return None

def get_transcript_from_db(conn: Optional[psycopg2.extensions.connection], video_id: str) -> Optional[str]:
    if not conn:
        return None
    
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT transcript FROM transcripts WHERE id = %s", (video_id,))
            result = cur.fetchone()
            return result[0] if result else None
    except psycopg2.Error as e:
        print(f"Database read error: {e}")
        return None

def save_transcript_to_db(conn: Optional[psycopg2.extensions.connection], video_id: str, transcript_text: str) -> None:
    if not conn:
        return

    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO transcripts (id, transcript)
                VALUES (%s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (video_id, transcript_text))
            conn.commit()
    except psycopg2.Error as e:
        print(f"Database write error: {e}")

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

def generate_youtube_transcript_params(video_id: str, asr: bool = True) -> str:
    if asr:
        inner_base64 = 'CgNhc3ISAmVuGgA%3D'
    else:
        inner_base64 = 'CgASAmVuGgA%3D'
    
    params = (
        b'\x0a' + bytes([len(video_id)]) + video_id.encode('ascii') +
        b'\x12' + bytes([len(inner_base64)]) + inner_base64.encode('ascii') +
        b'\x18\x01' +
        b'\x2a\x33engagement-panel-searchable-transcript-search-panel' +
        b'\x30\x01\x38\x01\x40\x01'
    )
    
    return urllib.parse.quote(base64.b64encode(params).decode('ascii'))

def fetch_youtube_transcript_text(video_id: str, asr: bool = True, timestamps: bool = False) -> str:
    params = generate_youtube_transcript_params(video_id, asr=asr)
    
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
    
    if not asr:
        payload["languageCode"] = "en"
    
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
    
    url = "https://www.youtube.com/youtubei/v1/get_transcript?prettyPrint=false"
    
    try:
        response = requests.post(url, json=payload, headers=headers)
    except requests.RequestException as e:
        raise ConnectionError(f"Network error while fetching transcript: {str(e)}")
    
    if response.status_code != 200:
        raise ValueError(f"Failed to fetch transcript: HTTP {response.status_code}")
    
    try:
        data = response.json()
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse transcript response JSON: {str(e)}")
    
    all_text = []
    
    try:
        actions = data.get('actions', [])
        for action in actions:
            if 'updateEngagementPanelAction' in action:
                panel = action['updateEngagementPanelAction']['content']['transcriptRenderer']
                body = panel['content']['transcriptSearchPanelRenderer']['body']['transcriptSegmentListRenderer']
                
                initial_segments = body.get('initialSegments', [])
                for segment in initial_segments:
                    if 'transcriptSegmentRenderer' in segment:
                        seg_data = segment['transcriptSegmentRenderer']
                        
                        start_time = seg_data.get('startTimeText', {}).get('simpleText', '')
                        text = seg_data['snippet']['runs'][0]['text']
                        
                        if timestamps:
                            if start_time:
                                formatted_segment = f"[{start_time}] {text}"
                            else:
                                formatted_segment = text
                            all_text.append(formatted_segment)
                        else:
                            all_text.append(text.strip())
                
                break
                
    except (KeyError, IndexError) as e:
        raise ValueError(f"Failed to parse transcript data - unexpected response structure: {str(e)}")
    
    if timestamps:
        return '\n'.join(all_text)
    
    return ' '.join(all_text)

# ======================================================================================================================
# HIGH-LEVEL FUNCTION FOR EXTERNAL USE
# ======================================================================================================================

def get_transcript(video_url_or_id: str, timestamps: bool = False) -> Optional[str]:
    if 'youtube.com' in video_url_or_id or 'youtu.be' in video_url_or_id:
        video_id = extract_video_id(video_url_or_id)
    else:
        video_id = video_url_or_id
    
    conn = get_db_connection()
    
    try:
        if conn:
            cached_transcript = get_transcript_from_db(conn, video_id)
            if cached_transcript:
                return cached_transcript
        
        transcript_text = None
        last_error = None
        
        try:
            transcript_text = fetch_youtube_transcript_text(video_id, asr=True, timestamps=timestamps)
            print(f"Transcript fetched (ASR) for video {video_id}")
        except Exception as asr_error:
            last_error = asr_error
            try:
                transcript_text = fetch_youtube_transcript_text(video_id, asr=False, timestamps=timestamps)
                print(f"Transcript fetched (manual) for video {video_id}")
            except Exception as manual_error:
                last_error = manual_error
                error_msg = str(manual_error).lower()
                if 'transcript' in error_msg or 'not available' in error_msg or 'disabled' in error_msg:
                    return None
                else:
                    raise
        
        if conn and transcript_text:
            save_transcript_to_db(conn, video_id, transcript_text)
            
        return transcript_text
    except (ValueError, ConnectionError):
        raise
    except Exception as e:
        raise RuntimeError(f"Unexpected error while fetching transcript: {str(e)}")
    finally:
        if conn:
            conn.close()
