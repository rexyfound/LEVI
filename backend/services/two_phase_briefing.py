import asyncio
import datetime
import time
from memory.memory_manager import get_latest_unconsumed_session, consume_session
from tools.parallel_search import parallel_web_search
from time_context import date_label

async def run_two_phase_briefing(event_bus=None) -> dict:
    """
    Execute two-phase morning/session briefing.
    Phase 1: Instant local greeting + session continuity memory.
    Phase 2: Async background fetch of today's headlines & updates.
    """
    hour = datetime.datetime.now().hour
    period = "morning" if 6 <= hour < 12 else "afternoon" if 12 <= hour < 18 else "evening"
    
    # --- PHASE 1: INSTANT GREETING & CONTINUITY ---
    latest_sess = get_latest_unconsumed_session()
    sess_text = ""
    if latest_sess:
        summary = latest_sess.get("summary", "")
        sess_text = f" Yesterday you were working on: '{summary}'."
        consume_session(latest_sess["id"])
        
    phase1_message = f"Good {period}, Sir.{sess_text} Initializing Phase 2 background telemetry..."
    
    if event_bus:
        await event_bus.emit("message", {"role": "assistant", "content": phase1_message, "phase": 1})
        await event_bus.emit("agent_state_changed", {"state": "VALIDATING"})

    # --- PHASE 2: ASYNC BACKGROUND NEWS & WEATHER FETCH ---
    await asyncio.sleep(0.5) # Non-blocking brief pause
    news_res = parallel_web_search("top news headlines today")
    headline_text = ""
    if news_res.get("success") and news_res.get("results"):
        top_item = news_res["results"][0]
        headline_text = f" Today's top headline: '{top_item.get('title')}' - {top_item.get('snippet', '')[:120]}..."
        
    phase2_message = f"Phase 2 Complete. Today is {date_label()}.{headline_text} All systems online and operational."

    if event_bus:
        await event_bus.emit("message", {"role": "assistant", "content": phase2_message, "phase": 2})
        await event_bus.emit("agent_state_changed", {"state": "COMPLETED"})

    return {
        "phase1": phase1_message,
        "phase2": phase2_message
    }
