import time
import psutil

# MARK: - CPU Load Extension

def get_cpu_usage(current_data: dict) -> dict:
    """
    Reads actual host CPU usage and determines trend state.
    """
    cpu_usage = psutil.cpu_percent()
    cpu_trend = current_data.get("trend", "stable")
    delta = cpu_usage - current_data.get("value", 35.0)
    if delta > 1.0:
        cpu_trend = "up"
    elif delta < -1.0:
        cpu_trend = "down"
    return {"value": cpu_usage, "trend": cpu_trend}

# MARK: - RAM Allocation Extension

def get_ram_usage(current_data: dict) -> dict:
    """
    Reads actual host Memory usage percentage and determines trend state.
    """
    ram_usage = psutil.virtual_memory().percent
    ram_trend = current_data.get("trend", "stable")
    ram_delta = ram_usage - current_data.get("value", 50.0)
    if ram_delta > 0.5:
        ram_trend = "up"
    elif ram_delta < -0.5:
        ram_trend = "down"
    return {"value": ram_usage, "trend": ram_trend}

# MARK: - Live Network Throughput Speedometer Extension

def get_network_traffic(current_data: dict) -> dict:
    """
    Reads host interface packets and calculates exact live download/upload speeds (in Mbps)
    based on the time delta since the last sample.
    """
    now = time.time()
    counters = psutil.net_io_counters()
    dl_bytes = counters.bytes_recv
    ul_bytes = counters.bytes_sent
    
    history = current_data.get("history", [])
    
    last_bytes_dl = current_data.get("_last_bytes_dl")
    last_bytes_ul = current_data.get("_last_bytes_ul")
    last_time = current_data.get("_last_time")
    
    speed_dl_mbps = 0.0
    speed_ul_mbps = 0.0
    
    if last_bytes_dl is not None and last_bytes_ul is not None and last_time is not None:
        time_diff = now - last_time
        if time_diff > 0:
            # Convert bytes transfer diff to bits rate -> Megabits per second (Mbps)
            speed_dl_mbps = ((dl_bytes - last_bytes_dl) * 8) / (1024 * 1024 * time_diff)
            speed_ul_mbps = ((ul_bytes - last_bytes_ul) * 8) / (1024 * 1024 * time_diff)
            
    # Keep speeds bounded at a minimum of 0.1 Mbps so the graph is drawn correctly
    speed_dl_mbps = max(0.1, speed_dl_mbps)
    speed_ul_mbps = max(0.1, speed_ul_mbps)
    
    history.append({
        "timestamp": now,
        "download": speed_dl_mbps,
        "upload": speed_ul_mbps
    })
    
    if len(history) > 15:
        history.pop(0)
        
    return {
        "history": history,
        "_last_bytes_dl": dl_bytes,
        "_last_bytes_ul": ul_bytes,
        "_last_time": now
    }
