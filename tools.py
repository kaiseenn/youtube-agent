"""
LangChain Tool Wrappers for YouTube Study Assistant
Wraps existing YouTube functions into LangChain-compatible tools for the agent.
"""

import json
import sys
from typing import Optional
from langchain.tools import tool

# Import existing YouTube functions
from functions.search import (
    search_youtube_videos,
    extract_videos,
    extract_continuation_token
)
from functions.transcript import (
    extract_video_id,
    fetch_youtube_transcript_text
)
from functions.comments import (
    get_video_page,
    extract_ytInitialData,
    extract_comment_token,
    fetch_comments,
    extract_comments,
    extract_next_continuation_token
)


# ======================================================================================================================
# TOOL 1: SEARCH YOUTUBE
# ======================================================================================================================

@tool
def search_youtube(query: str, max_results: int = 5, exclude_shorts: bool = True) -> str:
    """
    Search YouTube for videos related to a query. Use this when the user asks about a topic 
    and you need to find relevant educational videos.
    
    Args:
        query: The search term or topic to look for (e.g., "machine learning basics", "calculus derivatives")
        max_results: Number of video results to return (default: 5, max recommended: 10)
        exclude_shorts: Whether to filter out YouTube Shorts (default: True)
    
    Returns:
        JSON string containing a list of videos with title, channel, views, video_id, and description.
        Returns error message if search fails.
    
    Example usage:
        - User asks: "Find me videos about neural networks"
        - Tool call: search_youtube(query="neural networks explained", max_results=5)
    """
    print(f"🔍 Searching YouTube for: '{query}' (max {max_results} results)...", file=sys.stderr)
    
    try:
        # Initial search
        all_videos = []
        response = search_youtube_videos(query)
        
        if not response:
            return json.dumps({"error": "Failed to get search results from YouTube API"})
        
        response_data = response.json()
        all_videos.extend(extract_videos(response_data, exclude_shorts))
        continuation_token = extract_continuation_token(response_data)
        
        # Fetch more results if needed
        while len(all_videos) < max_results and continuation_token:
            print(f"   📥 Collected {len(all_videos)} videos, fetching more...", file=sys.stderr)
            response = search_youtube_videos(query, continuation=continuation_token)
            if not response:
                break
            
            response_data = response.json()
            all_videos.extend(extract_videos(response_data, exclude_shorts))
            continuation_token = extract_continuation_token(response_data)
        
        # Limit to requested number
        final_videos = all_videos[:max_results]
        
        print(f"✅ Found {len(final_videos)} videos", file=sys.stderr)
        
        # Return as JSON string for LLM to parse
        return json.dumps(final_videos, indent=2, ensure_ascii=False)
        
    except Exception as e:
        error_msg = f"Error searching YouTube: {str(e)}"
        print(f"❌ {error_msg}", file=sys.stderr)
        return json.dumps({"error": error_msg})


# ======================================================================================================================
# TOOL 2: GET TRANSCRIPT
# ======================================================================================================================

@tool
def get_transcript(video_url_or_id: str, include_timestamps: bool = False) -> str:
    """
    Extract the full transcript from a YouTube video. Use this when you need to analyze 
    the detailed content of a specific video.
    
    Args:
        video_url_or_id: Either a full YouTube URL or just the video ID (e.g., "dQw4w9WgXcQ")
        include_timestamps: Whether to include timestamps in the transcript (default: False)
    
    Returns:
        The full transcript text. If include_timestamps=True, format is "[HH:MM:SS] text".
        Returns error message if transcript is unavailable or video doesn't exist.
    
    Example usage:
        - After searching, to get details: get_transcript(video_url_or_id="abc123")
        - To study with timestamps: get_transcript(video_url_or_id="abc123", include_timestamps=True)
    """
    print(f"📝 Extracting transcript from video: {video_url_or_id}...", file=sys.stderr)
    
    try:
        # Extract video ID if URL was provided
        if 'youtube.com' in video_url_or_id or 'youtu.be' in video_url_or_id:
            video_id = extract_video_id(video_url_or_id)
        else:
            video_id = video_url_or_id
        
        print(f"   🎥 Video ID: {video_id}", file=sys.stderr)
        
        # Try ASR (auto-generated) transcript first
        try:
            transcript = fetch_youtube_transcript_text(
                video_id, 
                asr=True, 
                timestamps=include_timestamps
            )
            print(f"✅ Successfully extracted transcript ({len(transcript)} characters)", file=sys.stderr)
            return transcript
            
        except Exception as asr_error:
            # If ASR fails, try manual transcript
            print(f"   ⚠️  ASR transcript failed, trying manual transcript...", file=sys.stderr)
            try:
                transcript = fetch_youtube_transcript_text(
                    video_id, 
                    asr=False, 
                    timestamps=include_timestamps
                )
                print(f"✅ Successfully extracted manual transcript ({len(transcript)} characters)", file=sys.stderr)
                return transcript
            except Exception as manual_error:
                error_msg = f"No transcript available for this video. ASR error: {str(asr_error)}, Manual error: {str(manual_error)}"
                print(f"❌ {error_msg}", file=sys.stderr)
                return f"ERROR: {error_msg}"
    
    except ValueError as e:
        error_msg = f"Invalid video URL or ID: {str(e)}"
        print(f"❌ {error_msg}", file=sys.stderr)
        return f"ERROR: {error_msg}"
    
    except Exception as e:
        error_msg = f"Error fetching transcript: {str(e)}"
        print(f"❌ {error_msg}", file=sys.stderr)
        return f"ERROR: {error_msg}"


# ======================================================================================================================
# TOOL 3: GET COMMENTS
# ======================================================================================================================

@tool
def get_comments(video_url_or_id: str, max_comments: int = 10, sort_by_newest: bool = False) -> str:
    """
    Fetch comments from a YouTube video. Use this to get additional insights, explanations, 
    or common questions from the community about the video content.
    
    Args:
        video_url_or_id: Either a full YouTube URL or just the video ID
        max_comments: Number of comments to fetch (default: 10, max recommended: 20)
        sort_by_newest: If True, get newest comments; if False, get top comments (default: False)
    
    Returns:
        JSON string containing a list of comments with text, vote count, and published time.
        Returns error message if comments are disabled or unavailable.
    
    Example usage:
        - To see what viewers found helpful: get_comments(video_url_or_id="abc123", max_comments=10)
        - To see recent discussions: get_comments(video_url_or_id="abc123", sort_by_newest=True)
    """
    sort_type = "newest" if sort_by_newest else "top"
    print(f"💬 Fetching {max_comments} {sort_type} comments from: {video_url_or_id}...", file=sys.stderr)
    
    try:
        # Extract video ID if URL was provided
        if 'youtube.com' in video_url_or_id or 'youtu.be' in video_url_or_id:
            video_id = extract_video_id(video_url_or_id)
        else:
            video_id = video_url_or_id
        
        print(f"   🎥 Video ID: {video_id}", file=sys.stderr)
        
        # Step 1: Fetch video page
        html_content = get_video_page(video_id)
        if not html_content:
            return json.dumps({"error": "Failed to retrieve video page"})
        
        # Step 2: Extract initial data
        ytInitialData = extract_ytInitialData(html_content)
        if not ytInitialData:
            return json.dumps({"error": "Failed to extract video data"})
        
        # Step 3: Get initial continuation token
        continuation_token = extract_comment_token(ytInitialData, newest=sort_by_newest)
        if not continuation_token:
            return json.dumps({"error": "Comments may be disabled for this video"})
        
        # Step 4: Fetch comments in a loop
        all_comments = []
        is_initial_fetch = True
        
        while len(all_comments) < max_comments and continuation_token:
            if not is_initial_fetch:
                print(f"   📥 Collected {len(all_comments)} comments, fetching more...", file=sys.stderr)
            
            comments_data = fetch_comments(continuation_token)
            if not comments_data:
                break
            
            extracted = extract_comments(comments_data, is_initial=is_initial_fetch)
            all_comments.extend(extracted)
            
            continuation_token = extract_next_continuation_token(comments_data)
            is_initial_fetch = False
        
        # Limit to requested number
        final_comments = all_comments[:max_comments]
        
        print(f"✅ Fetched {len(final_comments)} comments", file=sys.stderr)
        
        return json.dumps(final_comments, indent=2, ensure_ascii=False)
    
    except ValueError as e:
        error_msg = f"Invalid video URL or ID: {str(e)}"
        print(f"❌ {error_msg}", file=sys.stderr)
        return json.dumps({"error": error_msg})
    
    except Exception as e:
        error_msg = f"Error fetching comments: {str(e)}"
        print(f"❌ {error_msg}", file=sys.stderr)
        return json.dumps({"error": error_msg})


# ======================================================================================================================
# TOOL LIST FOR AGENT
# ======================================================================================================================

# Export all tools as a list for easy import
TOOLS = [search_youtube, get_transcript, get_comments]

