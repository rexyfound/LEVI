import asyncio
import time
from memory.memory_manager import (
    load_memory,
    get_monitored_topics,
    update_topic_headline,
    add_monitored_topic,
    remove_monitored_topic
)
from tools.parallel_search import _fetch_ddg_search

BLOCKED_KEYWORDS = ["crypto", "bitcoin", "ethereum", "btc", "eth", "forex", "trading", "stocks", "solana", "memecoin"]

def is_blocked_topic(topic: str) -> bool:
    topic_lower = topic.lower()
    return any(kw in topic_lower for kw in BLOCKED_KEYWORDS)

def register_topic(topic: str) -> dict:
    if is_blocked_topic(topic):
        return {
            "success": False,
            "error": "Crypto and financial trading topics are blocked by monitoring policy."
        }
    return add_monitored_topic(topic)

def unregister_topic(topic: str) -> dict:
    return remove_monitored_topic(topic)

def list_topics() -> dict:
    topics = get_monitored_topics()
    return {"success": True, "topics": topics}

async def in_background_check_topics(event_bus=None):

    """
    Background worker that checks monitored topics periodically.
    Emits monitor_alert events when new headlines are discovered.
    """
    while True:
        try:
            topics = get_monitored_topics()
            for item in topics:
                topic = item.get("topic")
                last_headline = item.get("last_headline", "")
                
                # Fetch fresh DDG headline
                res = _fetch_ddg_search(f"{topic} news")
                if res.get("success") and res.get("results"):
                    first_res = res["results"][0]
                    snippet = first_res.get("snippet", "")
                    title = first_res.get("title", "")
                    current_headline = f"{title}: {snippet}" if title else snippet
                    
                    if current_headline and current_headline != last_headline:
                        update_topic_headline(topic, current_headline)
                        print(f"[BACKGROUND_MONITOR] New development for '{topic}': {title}")
                        
                        if event_bus:
                            await event_bus.emit("monitor_alert", {
                                "topic": topic,
                                "headline": current_headline,
                                "title": title,
                                "timestamp": time.time()
                            })
        except Exception as e:
            print(f"[BACKGROUND_MONITOR_ERROR] {e}")
            
        # Check every 60 minutes
        await asyncio.sleep(3600)
