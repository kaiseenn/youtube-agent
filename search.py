import requests
import json
import argparse

def search_youtube_videos(query):
    """
    Search YouTube videos using the internal API
    
    Args:
        query: Search query string
        
    Returns:
        Response JSON data
    """
    
    # YouTube search API endpoint
    url = "https://www.youtube.com/youtubei/v1/search?prettyPrint=false"
    
    # Request headers based on the provided structure
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
        "Referer": f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-Mode": "same-origin",
        "Sec-Fetch-Dest": "empty",
        "Sec-Ch-Ua": '"Not)A;Brand";v="8", "Chromium";v="138"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"'
    }
    
    # Request payload based on the provided structure
    payload = {
        "context": {
            "client": {
                "hl": "en",
                "gl": "CA",
                "remoteHost": "149.88.98.167",
                "deviceMake": "",
                "deviceModel": "",
                "visitorData": "CgtuMGtDeGI1N1AyTSjludXDBjIKCgJDQRIEGgAgQw%3D%3D",
                "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36,gzip(gfe)",
                "clientName": "WEB",
                "clientVersion": "2.20250710.09.00",
                "osName": "Windows",
                "osVersion": "10.0",
                "originalUrl": f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}",
                "platform": "DESKTOP",
                "clientFormFactor": "UNKNOWN_FORM_FACTOR",
                "userInterfaceTheme": "USER_INTERFACE_THEME_LIGHT",
                "timeZone": "America/Toronto",
                "browserName": "Chrome",
                "browserVersion": "138.0.0.0",
                "acceptHeader": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "screenWidthPoints": 1247,
                "screenHeightPoints": 1277,
                "screenPixelDensity": 1,
                "screenDensityFloat": 1,
                "utcOffsetMinutes": -240,
                "memoryTotalKbytes": "8000000",
                "mainAppWebInfo": {
                    "graftUrl": f"/results?search_query={query.replace(' ', '+')}",
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
                "consistencyTokenJars": [],
                "internalExperimentFlags": []
            }
        },
        "query": query
    }
    
    try:
        # Make the POST request
        response = requests.post(url, json=payload, headers=headers)
        
        if response.status_code != 200:
            print(f"Error: HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
        # Return the JSON response
        return response.json()
        
    except Exception as e:
        print(f"Request failed: {str(e)}")
        return None

# Command Line Interface
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Search YouTube videos'
    )
    
    parser.add_argument(
        'query',
        help='Search query'
    )
    
    args = parser.parse_args()
    
    print(f"Searching YouTube for: {args.query}\n")
    
    # Search for videos
    response_data = search_youtube_videos(args.query)
    
    if response_data:
        print("=== SEARCH RESPONSE ===")
        print(json.dumps(response_data, indent=2))
    else:
        print("Failed to get search results")
        exit(1)
    
    exit(0) 