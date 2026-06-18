import httpx
import src.state as state

async def get_status(current_state: dict, card_config: dict) -> dict:
    config = card_config.get("apiConfig", {})
    url = config.get("url", "").rstrip("/")
    password = config.get("password", "")
    if not url or "YOUR_" in password or not password:
        raise ValueError("Deluge credentials not configured")
        
    json_url = f"{url}/json"
    
    async with httpx.AsyncClient() as client:
        # 1. Login to obtain session cookies
        login_payload = {
            "method": "auth.login",
            "params": [password],
            "id": 1
        }
        login_resp = await client.post(json_url, json=login_payload, timeout=2.0)
        login_resp.raise_for_status()
        if not login_resp.json().get("result"):
            raise PermissionError("Deluge login credentials rejected")
            
        # 2. Fetch UI status updates
        update_payload = {
            "method": "web.update_ui",
            "params": [
                ["name", "progress", "state", "download_payload_rate", "upload_payload_rate", "eta"],
                {}
            ],
            "id": 2
        }
        update_resp = await client.post(json_url, json=update_payload, timeout=3.0)
        update_resp.raise_for_status()
        
        result = update_resp.json().get("result") or {}
        torrents_dict = result.get("torrents") or {}
        
        torrents_list = []
        total_down_rate = 0.0
        total_up_rate = 0.0
        
        for torrent_id, t in torrents_dict.items():
            name = t.get("name", "Unknown Torrent")
            raw_progress = t.get("progress", 0.0)
            progress = min(1.0, max(0.0, raw_progress / 100.0))
            status = t.get("state", "Downloading")
            
            # Deluge reports rates in Bytes/second -> convert to MB/s
            speed_down_mb = t.get("download_payload_rate", 0) / (1024 * 1024)
            speed_up_mb = t.get("upload_payload_rate", 0) / (1024 * 1024)
            
            total_down_rate += speed_down_mb
            total_up_rate += speed_up_mb
            
            eta_sec = t.get("eta", 0)
            if status == "Downloading":
                if eta_sec > 0:
                    m, s = divmod(int(eta_sec), 60)
                    h, m = divmod(m, 60)
                    eta_str = f"{h}h {m}m" if h > 0 else f"{m}m {s}s"
                    speed_text = f"DL: {speed_down_mb:.1f} MB/s • ETA: {eta_str}"
                else:
                    speed_text = f"DL: {speed_down_mb:.1f} MB/s"
            elif status == "Seeding":
                speed_text = f"UL: {speed_up_mb:.1f} MB/s"
            else:
                speed_text = f"{status}"
                
            torrents_list.append({
                "id": torrent_id,
                "name": name,
                "progress": progress,
                "progressPercentText": f"{raw_progress:.1f}%",
                "status": status,
                "speedDown": speed_down_mb,
                "speedUp": speed_up_mb,
                "speedText": speed_text
            })
            
        return {
            "downloadSpeedText": f"{total_down_rate:.1f} MB/s",
            "uploadSpeedText": f"{total_up_rate:.1f} MB/s",
            "torrents": torrents_list
        }

async def handle_action(action: str, item_id: str, card_config: dict) -> None:
    config = card_config.get("apiConfig", {})
    url = config.get("url", "").rstrip("/")
    password = config.get("password", "")
    if not url or "YOUR_" in password or not password:
        raise ValueError("Deluge credentials not configured")
        
    json_url = f"{url}/json"
    
    async with httpx.AsyncClient() as client:
        # 1. Login to establish cookie
        login_resp = await client.post(json_url, json={
            "method": "auth.login",
            "params": [password],
            "id": 1
        }, timeout=3.0)
        login_resp.raise_for_status()
        
        # 2. Send pause/resume or remove method
        if action == "toggle" and item_id:
            torrents = state.card_data.get("deluge_torrents", {}).get("torrents", [])
            matched = [t for t in torrents if t["id"] == item_id]
            current_status = matched[0]["status"] if matched else "Paused"
            
            method = "core.pause_torrent" if current_status != "Paused" else "core.resume_torrent"
            
            resp = await client.post(json_url, json={
                "method": method,
                "params": [[item_id]],
                "id": 2
            }, timeout=5.0)
            resp.raise_for_status()
            
        elif action == "delete" and item_id:
            resp = await client.post(json_url, json={
                "method": "core.remove_torrent",
                "params": [[item_id], False],
                "id": 3
            }, timeout=5.0)
            resp.raise_for_status()
