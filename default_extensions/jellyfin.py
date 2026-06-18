import httpx
import asyncio

async def get_playback(current_state: dict, card_config: dict) -> dict:
    config = card_config.get("apiConfig", {})
    url = config.get("url", "").rstrip("/")
    api_key = config.get("apiKey", "")
    if not url or "YOUR_" in api_key or not api_key:
        raise ValueError("Jellyfin credentials not configured")
    
    headers = {"X-MediaBrowser-Token": api_key}
    
    async with httpx.AsyncClient() as client:
        # 1. Fetch active sessions (playing streams)
        sessions_resp = await client.get(f"{url}/Sessions", headers=headers, timeout=2.0)
        sessions_resp.raise_for_status()
        sessions = sessions_resp.json()
        
        active_streams = []
        for s in sessions:
            playing_item = s.get("NowPlayingItem")
            if playing_item is None:
                continue
            
            session_id = s.get("Id", "")
            title = playing_item.get("Name", "Unknown Title")
            
            series_name = playing_item.get("SeriesName")
            if series_name:
                season = playing_item.get("ParentIndexNumber", 1)
                episode = playing_item.get("IndexNumber", 1)
                ep_name = playing_item.get("Name", "")
                subtitle = f"{series_name} • S{season:02d}E{episode:02d} • {ep_name}"
            else:
                prod_year = playing_item.get("ProductionYear", "")
                subtitle = f"{prod_year}" if prod_year else "Movie"
                
            play_state = s.get("PlayState", {})
            is_paused = play_state.get("IsPaused", False)
            status = "Paused" if is_paused else "Playing"
            
            position = play_state.get("PositionTicks", 0)
            runtime = playing_item.get("RunTimeTicks", 0)
            progress = 0.0
            if runtime > 0:
                progress = min(1.0, max(0.0, position / runtime))
                
            item_id = playing_item.get("Id", "")
            image_url = f"{url}/Items/{item_id}/Images/Primary" if item_id else ""
            
            active_streams.append({
                "id": session_id,
                "title": title,
                "subtitle": subtitle,
                "user": s.get("UserName", "Unknown User"),
                "progress": progress,
                "status": status,
                "imageUrl": image_url
            })
            
        # 2. Fetch recently added movies, series, and episodes
        recent_url = f"{url}/Items?Limit=4&Recursive=true&IncludeItemTypes=Movie,Series,Episode&SortBy=DateCreated&SortOrder=Descending"
        recent_resp = await client.get(recent_url, headers=headers, timeout=2.0)
        recent_resp.raise_for_status()
        recent_items = recent_resp.json().get("Items", [])
        
        recently_added = []
        for item in recent_items:
            item_id = item.get("Id", "")
            item_type = item.get("Type", "Movie")
            recently_added.append({
                "id": item_id,
                "title": item.get("Name", "Unknown Title"),
                "type": item_type,
                "imageUrl": f"{url}/Items/{item_id}/Images/Primary" if item_id else ""
            })
            
        return {
            "activeStreams": active_streams,
            "recentlyAdded": recently_added
        }

async def handle_action(action: str, item_id: str, card_config: dict) -> None:
    config = card_config.get("apiConfig", {})
    url = config.get("url", "").rstrip("/")
    api_key = config.get("apiKey", "")
    if not url or "YOUR_" in api_key or not api_key:
        raise ValueError("Jellyfin credentials not configured")
        
    if action == "toggle" and item_id:
        async with httpx.AsyncClient() as client:
            play_url = f"{url}/Sessions/{item_id}/Playing/PlayPause"
            headers = {"X-MediaBrowser-Token": api_key}
            resp = await client.post(play_url, headers=headers, timeout=5.0)
            resp.raise_for_status()

async def get_library_stats(current_state: dict, card_config: dict) -> dict:
    config = card_config.get("apiConfig", {})
    url = config.get("url", "").rstrip("/")
    api_key = config.get("apiKey", "")
    if not url or "YOUR_" in api_key or not api_key:
        raise ValueError("Jellyfin credentials not configured")
        
    headers = {"X-MediaBrowser-Token": api_key}
    
    async with httpx.AsyncClient() as client:
        async def get_count(item_type: str) -> int:
            resp = await client.get(
                f"{url}/Items?IncludeItemTypes={item_type}&Recursive=true&Limit=0",
                headers=headers,
                timeout=3.0
            )
            resp.raise_for_status()
            return resp.json().get("TotalRecordCount", 0)
            
        movies_count, series_count, episodes_count = await asyncio.gather(
            get_count("Movie"),
            get_count("Series"),
            get_count("Episode")
        )
        
        return {
            "moviesCount": movies_count,
            "seriesCount": series_count,
            "episodesCount": episodes_count
        }
