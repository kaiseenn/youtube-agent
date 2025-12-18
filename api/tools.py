import json
from langchain.tools import tool

from functions.search import search_videos
from functions.transcript import get_transcript as get_transcript_function
from functions.comments import get_comments as get_comments_function

@tool
def search_youtube(query: str, max_results: int = 10, exclude_shorts: bool = True) -> str:
    """
    Search YouTube for videos related to a query. Use this when the user asks about a topic 
    and you need to find relevant educational videos.
    
    Args:
        query: The search term or topic to look for (e.g., "machine learning basics", "calculus derivatives")
        max_results: Number of video results to return (default: 10, max recommended: 20)
        exclude_shorts: Whether to filter out YouTube Shorts (default: True)
    
    Returns:
        JSON string containing a list of videos with title, channel, views, video_id, and description.
        Returns error message if search fails.
    
    Example usage:
        - User asks: "Find me videos about neural networks"
        - Tool call: search_youtube(query="neural networks explained", max_results=5)
    """

    
    try:
        # Call the high-level search function
        videos = search_videos(query, max_results=max_results, exclude_shorts=exclude_shorts)
        
        if videos is None:
            return json.dumps({"message": "No videos found for the query", "results": []})
        
        # Return as JSON string for LLM to parse
        return json.dumps(videos, indent=2, ensure_ascii=False)
        
    except (ValueError, ConnectionError, RuntimeError) as e:
        error_msg = f"Error searching YouTube: {str(e)}"
        return json.dumps({"error": error_msg})
    
    except Exception as e:
        error_msg = f"Unexpected error searching YouTube: {str(e)}"
        return json.dumps({"error": error_msg})


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

    
    try:
        # Call the high-level transcript function
        transcript = get_transcript_function(video_url_or_id, timestamps=include_timestamps)
        
        if transcript is None:
            return "ERROR: Transcript is not available for this video (may be disabled or not yet generated)"
        
        return transcript
    
    except ValueError as e:
        error_msg = f"Invalid video URL or parsing error: {str(e)}"
        return f"ERROR: {error_msg}"
    
    except ConnectionError as e:
        error_msg = f"Network error while fetching transcript: {str(e)}"
        return f"ERROR: {error_msg}"
    
    except RuntimeError as e:
        error_msg = f"Unexpected error fetching transcript: {str(e)}"
        return f"ERROR: {error_msg}"
    
    except Exception as e:
        error_msg = f"Unknown error fetching transcript: {str(e)}"
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
    
    try:
        # Call the high-level comments function
        comments = get_comments_function(video_url_or_id, max_comments=max_comments, sort_by_newest=sort_by_newest)
        
        if comments is None:
            return json.dumps({"message": "Comments are disabled or unavailable for this video", "comments": []})
        
        return json.dumps(comments, indent=2, ensure_ascii=False)
    
    except ValueError as e:
        error_msg = f"Invalid video URL or parsing error: {str(e)}"
        return json.dumps({"error": error_msg})
    
    except ConnectionError as e:
        error_msg = f"Network error while fetching comments: {str(e)}"
        return json.dumps({"error": error_msg})
    
    except RuntimeError as e:
        error_msg = f"Unexpected error fetching comments: {str(e)}"
        return json.dumps({"error": error_msg})
    
    except Exception as e:
        error_msg = f"Unknown error fetching comments: {str(e)}"
        return json.dumps({"error": error_msg})

TOOLS = [search_youtube, get_transcript, get_comments]

