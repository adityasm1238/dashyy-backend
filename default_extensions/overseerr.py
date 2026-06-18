import httpx

async def get_requests(current_state: dict, card_config: dict) -> dict:
    config = card_config.get("apiConfig", {})
    url = config.get("url", "").rstrip("/")
    api_key = config.get("apiKey", "")
    if not url or "YOUR_" in api_key or not api_key:
        raise ValueError("Overseerr credentials not configured")
    
    headers = {"X-Api-Key": api_key}
    
    async with httpx.AsyncClient() as client:
        # 1. Fetch pending requests
        req_url = f"{url}/api/v1/request?filter=pending&take=5&skip=0"
        resp = await client.get(req_url, headers=headers, timeout=2.0)
        resp.raise_for_status()
        results = resp.json().get("results", [])
        
        requests_list = []
        for r in results:
            req_id = str(r.get("id", ""))
            media = r.get("media", {})
            media_type = media.get("mediaType", "movie")
            
            req_media = r.get("movie") or r.get("tv")
            title = "Unknown Request"
            poster_path = ""
            
            if req_media:
                title = req_media.get("title") or req_media.get("name") or "Unknown"
                poster_path = req_media.get("posterPath") or ""
                
            image_url = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else ""
            
            user = r.get("requestedBy", {})
            requester_name = user.get("displayName") or user.get("email") or "Requester"
            
            requests_list.append({
                "id": req_id,
                "title": title,
                "type": "Movie" if media_type == "movie" else "TV Show",
                "imageUrl": image_url,
                "requester": requester_name
            })
            
        # 2. Fetch total stats counts
        count_url = f"{url}/api/v1/request/count"
        count_resp = await client.get(count_url, headers=headers, timeout=2.0)
        count_resp.raise_for_status()
        counts = count_resp.json()
        
        return {
            "pendingCount": counts.get("pending", len(requests_list)),
            "approvedCount": counts.get("approved", 24),
            "requests": requests_list
        }

async def handle_action(action: str, item_id: str, card_config: dict) -> None:
    config = card_config.get("apiConfig", {})
    url = config.get("url", "").rstrip("/")
    api_key = config.get("apiKey", "")
    if not url or "YOUR_" in api_key or not api_key:
        raise ValueError("Overseerr credentials not configured")
        
    if not item_id:
        return
        
    headers = {"X-Api-Key": api_key}
    
    async with httpx.AsyncClient() as client:
        if action == "approve":
            approve_url = f"{url}/api/v1/request/{item_id}/approve"
            resp = await client.post(approve_url, headers=headers, timeout=5.0)
            resp.raise_for_status()
        elif action == "decline":
            decline_url = f"{url}/api/v1/request/{item_id}"
            resp = await client.delete(decline_url, headers=headers, timeout=5.0)
            resp.raise_for_status()
