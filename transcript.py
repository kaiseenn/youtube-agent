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
    
    # Build the request payload with complete parameters from working request
    payload = {
        "context": {
            "client": {
                "hl": "en",
                "gl": "CA",
                "remoteHost": "104.28.249.113",
                "deviceMake": "Apple",
                "deviceModel": "",
                "visitorData": "Cgs2Sk55ZTFwRTBHMCiHkpHKBjIKCgJDQRIEGgAgD2LfAgrcAjE0LllUPWhFTnVQcWt3VENGeHFlMWdFMzUtU3VzNDFMRGxZZVZyckx0X3I5ZF9laHFtVWNMTGxhZ1Z6MEhiblpaSy11WGZydzFTdV8zd1RDMFdqWFdPZjFZd0tibGY2QWFic2NyLW5kVlpOWmlzOTRON0lzMTdxanRoTERPMlJmRGRNbmJ3ZFpvQUNVLUFNUzl5azlNRUhoUkU3NnlqQVR5alBWaE0xdGxBV3JIZjE3SlVkbGJtZElmNm5KS0VtRUx3cG9iOHJJaXFPVVZWMVZITi1ZbXUwV2FCRzBtN2QwR2gyTVIxc2szVy1SaTdaOGxzdXBpSEtBeFNaODIycTdrMGFkc19iWUtON194WV9NWDJLZFRZMVZDeDVsYU5SdEFtMVJJYlU2cURwOUFNQzVmcWNyRktXaExaS0s3N3Y4TW5UTmN2bnJvX3FCNEYyaFJUNmlCaHZpZXI5UQ%3D%3D",
                "userAgent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36,gzip(gfe)",
                "clientName": "WEB",
                "clientVersion": "2.20251215.05.00",
                "osName": "Macintosh",
                "osVersion": "10_15_7",
                "originalUrl": f"https://www.youtube.com/shorts/aHIfnLRwZpU",
                "platform": "DESKTOP",
                "clientFormFactor": "UNKNOWN_FORM_FACTOR",
                "configInfo": {
                    "appInstallData": "CIeSkcoGEIeD0BwQlIPQHBC8pNAcEJ3XzxwQlPLPHBDxtNAcELyzgBMQ2JbQHBC36v4SELeGzxwQ2sHQHBCL988cELy_0BwQh6zOHBDYrtAcEInorgUQq53PHBDmh9AcELvZzhwQy9GxBRDxzM8cEK7WzxwQ8rPQHBDxxNAcEPCcsAUQ5uDPHBDevM4cEMq70BwQ0sHQHBDa984cEJ3QsAUQudnOHBDT4a8FEJu40BwQovvPHBDI988cEParsAUQg6zQHBDGvYATENq00BwQzOvPHBCJsM4cEIOe0BwQ8p3QHBDhwYATEPyyzhwQzrPQHBDgzbEFEL2KsAUQm8LQHBDR4M8cEIiHsAUQgc3OHBCmmrAFEKXd_xIQjLDQHBCmttAcELOQzxwQzdGxBRC0wdAcELjA0BwQ4tSuBRC9mbAFEPjE0BwQmbnQHBCZjbEFENiF0BwQj7nQHBDDkdAcENqu0BwQo4W4IhCon6kXEMe20BwQjOnPHBDBj9AcEJX3zxwQ0r3QHBDJ968FEL22rgUQt8nPHBCCj88cEMT0zxwQ5aTQHBCUttAcELjkzhwQzN-uBRCU_rAFEJbbzxwQrKzQHBDCwdAcEMux0BwQvsTQHBC8vtAcEMm00BwqbENBTVNTeFZBLVpxLURMaVVFb1lPcWdMTUJiX0I1Z3Z3c1JLSFRES2dyQVFEeTc0Ri1qbjVnZ2FnQnFJdW1pSHhUODRQN1Z6MUxfWVBoUlRpSS02ZEJlSVd4aXFETHVrVG5rdUNLQVlkQnc9PTAA",
                    "coldConfigData": "CIeSkcoGEOu6rQUQxIWuBRC9tq4FEOLUrgUQvYqwBRDwnLAFEI3MsAUQndCwBRDP0rAFEOP4sAUQr6fOHBD8ss4cELeGzxwQq53PHBD5xs8cENrTzxwQndfPHBDH2s8cELDgzxwQz-DPHBDl588cEOfnzxwQ_vfPHBCUg9AcEP2T0BwQk5XQHBCGntAcEM6s0BwQjLDQHBC4sNAcEMm00BwQ2rTQHBDxtNAcEPm00BwQobXQHBCmtdAcEKa20BwQx7bQHBCbuNAcEOq40BwQmbnQHBD8utAcEJS70BwQyrvQHBC8vtAcELy_0BwQuMDQHBDCwdAcENrB0BwQm8LQHBCfwtAcELLD0BwQvsTQHBDxxNAcEPjE0BwQ6MXQHBDGx9AcEKOFuCIaMkFDRFNSMlE2NTNQd0t5WG0tM2tfc1dDZHpqNWhiNnVNUGNlMDRTbFB0WV9fa2wxRV9BIjJBQ0RTUjJRNjUzUHdLeVhtLTNrX3NXQ2R6ajVoYjZ1TVBjZTA0U2xQdFlfX2tsMUVfQSqYAUNBTVNiZzB1dU4yM0FxUVo3eW5ITnBtU21oRDdGbzAyX2lPbkRjZ0FyQXhxTlBZWXFBTFpGN1VOQTYwTjh3QVZScWJldFItUm5BWFZ4Z1NVbkFUUHdnQ1Bwd2I5MUFZeXo0QUYyYVFHQTZLeUJjcExCckJ2aHdQR0NmTURpT1FGeTBvRWtyNEdtajNxTVpJRlhmeUNCdkZp",
                    "coldHashData": "CIeSkcoGEhQxMjE4NDI3Njg0MDg0MDg4Njk2MBiHkpHKBjIyQUNEU1IyUTY1M1B3S3lYbS0za19zV0Nkemo1aGI2dU1QY2UwNFNsUHRZX19rbDFFX0E6MkFDRFNSMlE2NTNQd0t5WG0tM2tfc1dDZHpqNWhiNnVNUGNlMDRTbFB0WV9fa2wxRV9BQpgBQ0FNU2JnMHV1TjIzQXFRWjd5bkhOcG1TbWhEN0ZvMDJfaU9uRGNnQXJBeHFOUFlZcUFMWkY3VU5BNjBOOHdBVlJxYmV0Ui1SbkFYVnhnU1VuQVRQd2dDUHB3YjkxQVl5ejRBRjJhUUdBNkt5QmNwTEJyQnZod1BHQ2ZNRGlPUUZ5MG9Fa3I0R21qM3FNWklGWGZ5Q0J2Rmk%3D",
                    "hotHashData": "CIeSkcoGEhQxNzczMjcxMDE3NjgzMDk3MjU1MRiHkpHKBiiU5PwSKKXQ_RIo2Zn-EijIyv4SKLfq_hIopd3_EijLkYATKLWbgBMo2LCAEyiTtIATKLC3gBMopbiAEyjGvYATKNq9gBMouMGAEyjhwYATKLLCgBMoqJ-pFzIyQUNEU1IyUTY1M1B3S3lYbS0za19zV0Nkemo1aGI2dU1QY2UwNFNsUHRZX19rbDFFX0E6MkFDRFNSMlE2NTNQd0t5WG0tM2tfc1dDZHpqNWhiNnVNUGNlMDRTbFB0WV9fa2wxRV9BQjhDQU1TSmcwSm90ZjZGYTdCQnV1YkJvUU55UVlWRTkzUHdnemk5Z19jcWVZTGpKY2s2UTYzQnVNeg%3D%3D"
                },
                "userInterfaceTheme": "USER_INTERFACE_THEME_LIGHT",
                "browserName": "Chrome",
                "browserVersion": "142.0.0.0",
                "acceptHeader": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "deviceExperimentId": "ChxOelU0TlRJMk56azJPRFU0T1RreU5qWXlPQT09EIeSkcoGGIeSkcoG",
                "rolloutToken": "CND9yM3F9rTqLhDug8ua48eRAxjug8ua48eRAw%3D%3D",
                "screenWidthPoints": 1200,
                "screenHeightPoints": 787,
                "screenPixelDensity": 2,
                "screenDensityFloat": 2,
                "utcOffsetMinutes": -300,
                "connectionType": "CONN_CELLULAR_4G",
                "memoryTotalKbytes": "8000000",
                "mainAppWebInfo": {
                    "graftUrl": f"https://www.youtube.com/watch?v={video_id}",
                    "pwaInstallabilityStatus": "PWA_INSTALLABILITY_STATUS_UNKNOWN",
                    "webDisplayMode": "WEB_DISPLAY_MODE_BROWSER",
                    "isWebNativeShareAvailable": True
                },
                "timeZone": "America/Toronto"
            },
            "user": {
                "lockedSafetyMode": False
            },
            "request": {
                "useSsl": True,
                "internalExperimentFlags": [],
                "consistencyTokenJars": [],
                "attestationResponseData": {
                    "challenge": "a=6&a2=10&b=d_ghSGCrwG-deaiQqEHtlC574PE&c=1766082823&d=1&t=21600&c1a=1&c6a=1&c6b=1&hh=HVyY0I5daawFt8XOjNt2e4snoXkoZQGdaIbHkyFHm4E",
                    "webResponse": "$_WI5YjpRAAZhipLMQYreNttqIg-M6K-nADQBEArZ1H1oV98P-5tVXi_zn4tdTenHGbi-z7iDj-SSZvxPu1BCbdO_RvcwY-vIk_bbDahXngAAAJ3OAAAAAvQBB-IAVM0wJOwEwpXcKNhhHy47Td-hOHuvZvviT70cPGejqgVMQ6PVXhqTETSNtHd3PVb-ih7lE9VAwsjZ-J6zPrR0Smam9udGkL69deY7OC6kLqgH8qulLwUFAiGXnIk5ZzRvtMczwRR1NL7f0qO7IKUukuKj1x1iX1sjyUtcxKs7KBdYnrn6HKSHm06fxBGh1JnVvnDvVYESOXF4WHoD8Cb58BATQXJtCM2sh0WMWpZixgEUEMRxJrT7nTu2nxc-SKkABG4s60FhNH_BB5pipcbGf2LUayvBursjz3p8Ja2DkYGT85pxy7X7mBdETZz-ER5nXXDAZwa7xtN8sLlfVp6H7fQa62TbbpCp9brN9aWNEhDQesc7aJl3_iAiXKZuYSCKnjBGUX59yuPHZnHdNWn60u3igs8TG_Mk3hppnck3rzRr9ZeGuM_X-F2ITWeuoFjkSVg6Xm1fj2ffflxTC6oWbszuWTg-FeT14sNBz7pAaNMpUaSl4LmwZUiXPBvgX-kk_dq_bcHgyf5DAQr267h8rC6kFgHWszXhZTWpwz-d_tCG5IxWjBV-L0egb3GFiapAmnFYo4VONpTkCtRKojMwuImj4Lw9o5gSwRvGyZ4SzJBOEsW6vfK74B5lzfvrgDY64tVEXZ9Omcnq0r_JVlUyKhXzqTiSuK5O_rrSscT7svEMFxd-XbIqP762H-9ftwY7TTuf_GVRb06eVOcgEh0O0Iz2F1OvYTheb2lXxdcKj1yucp1Z595TGm4_58JeEGp-592WTo8Q7XQTorccW3VGHXHJ8Ib2o9MBlXm0xUGeXv5TRnny7-UTMJBrikw4P3oO5b8xO0lX7X0kLiaaWtELpUF_M3M2JlFydXOR84LmexRJ2hzLvcqSU5Z5RzSZuFmiFzxDq3TJAZw25POs9mT36O3zDqZjgPVnmRhFy3-6VeS75F_xMy15M-UjOyNO8cQYN0cOiupU4G81W5uDW4OZZZOxpq6g-ttl7d9QvarTGAYgkGE-UOmHkBkjQZhJj2Olb5TP_NPYOva6msWhyoPhuXRJ-c8ch_FXtcfomNb4tUUbdul0s3adnf53Msoobp38DNb8iq89VfWDbrz9GjEWUkGGTJOJ1rgKLH9WfcNhgpQVPM4wA1JRyORlgFAVJGUudvvcfgXIjh3hDz7mDho8YUq9D5DWPJdtuORXdkWeouWaEl22oZNqJyNtkn4tq7OXLIDjddAzgMGw0RJRZPptbQvc_rRqmRRRyIm74ANzgi-gvppUEDxvBvU17_0e9mGeUouKJ-28675ceJYh0Y8y0tPnfYdjR_zdAVcjPBjIzqvM06498T2ID7-3KUGigCyPYWX1LTMnNO1JJiV9z7uPkDuvgWMC33d_YSz_l9S1sE_-XoStreUycq_KQ9DaZ5dd7eJBUNiMspvnorBE6lGHl775-qYJIPU1q86_uvG3U1mT1ZtPb-7qwl9lQyFGK7bDQi2nQUOQrSo9Je8F2ook9xzm6wrF5MaRbqqWhf9B9akNJroRBTjlKFeA9ewUQMsqx6jEBZTwrlYSWmcIwj2KvIFShy8JjjVBBToymN_Pxe3uXE_XPF00NSJrCXnv27h-_bj0cizeGjjUP-f5WZ3VUE1QURkhb--9BAvCVOx5rSn2Cpjvm0JtYJNmlj26ZKxQGp-UwjHaKkwZxhJBkp5ILXENPwpeITUgVHEd94s5FOeQB1ImTg84HmCXJJZVOZ5QfsPFgwWjZf0QlVetIMbYhxzPFE0meaVVb8pzNKEKxy82K9ykFyuh3yGEj5CKhdvqJtHwGXpjbfYDoGd4uJZALfQbscXHigxOm5Y"
                }
            }
        },
        "params": params,
        "languageCode": "en",
        "name": "Default",
        "externalVideoId": video_id
    }
    
    # Headers with all Sec-Ch-* and additional headers from working request
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
        "Accept": "*/*",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "X-Youtube-Client-Name": "1",
        "X-Youtube-Client-Version": "2.20251215.05.00",
        "X-Youtube-Bootstrap-Logged-In": "false",
        "X-Goog-Visitor-Id": "Cgs2Sk55ZTFwRTBHMCiHkpHKBjIKCgJDQRIEGgAgD2LfAgrcAjE0LllUPWhFTnVQcWt3VENGeHFlMWdFMzUtU3VzNDFMRGxZZVZyckx0X3I5ZF9laHFtVWNMTGxhZ1Z6MEhiblpaSy11WGZydzFTdV8zd1RDMFdqWFdPZjFZd0tibGY2QWFic2NyLW5kVlpOWmlzOTRON0lzMTdxanRoTERPMlJmRGRNbmJ3ZFpvQUNVLUFNUzl5azlNRUhoUkU3NnlqQVR5alBWaE0xdGxBV3JIZjE3SlVkbGJtZElmNm5KS0VtRUx3cG9iOHJJaXFPVVZWMVZITi1ZbXUwV2FCRzBtN2QwR2gyTVIxc2szVy1SaTdaOGxzdXBpSEtBeFNaODIycTdrMGFkc19iWUtON194WV9NWDJLZFRZMVZDeDVsYU5SdEFtMVJJYlU2cURwOUFNQzVmcWNyRktXaExaS0s3N3Y4TW5UTmN2bnJvX3FCNEYyaFJUNmlCaHZpZXI5UQ%3D%3D",
        "X-Client-Data": "CNuBywE=",
        "Origin": "https://www.youtube.com",
        "Referer": f"https://www.youtube.com/watch?v={video_id}",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "same-origin",
        "Sec-Fetch-Dest": "empty",
        "Sec-Ch-Ua": '"Not_A Brand";v="99", "Chromium";v="142"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"macOS"',
        "Sec-Ch-Ua-Platform-Version": '""',
        "Sec-Ch-Ua-Full-Version": '""',
        "Sec-Ch-Ua-Arch": '""',
        "Sec-Ch-Ua-Model": '""',
        "Sec-Ch-Ua-Bitness": '""',
        "Sec-Ch-Ua-Wow64": "?0",
        "Sec-Ch-Ua-Form-Factors": "",
        "Sec-Ch-Ua-Full-Version-List": "",
        "Sec-Ch-Viewport-Width": "1200",
        "Sec-Ch-Dpr": "2",
        "Device-Memory": "8",
        "Priority": "u=1, i"
    }
    
    # Make the request
    url = "https://www.youtube.com/youtubei/v1/get_transcript?prettyPrint=false"
    response = requests.post(url, json=payload, headers=headers)
    
    # Print response details for debugging
    print(f"Response Status Code: {response.status_code}")
    print(f"Response Body: {response.text}")
    
    if response.status_code != 200:
        raise Exception(f"Failed to fetch transcript: {response}")
    
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
                        
                        # Extract start time and text
                        start_time = seg_data.get('startTimeText', {}).get('simpleText', '')
                        text = seg_data['snippet']['runs'][0]['text']
                        
                        # Format as [Time] transcript
                        if start_time:
                            formatted_segment = f"[{start_time}] {text}"
                        else:
                            formatted_segment = text
                            
                        all_text.append(formatted_segment)
                
                break
                
    except (KeyError, IndexError) as e:
        raise Exception(f"Failed to parse transcript data: {str(e)}")
    
    # Join all text with newlines for better readability
    return '\n'.join(all_text)

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