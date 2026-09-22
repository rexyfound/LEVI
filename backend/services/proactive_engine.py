import asyncio
import datetime
import random
import time
from memory.memory_manager import (
    get_latest_unconsumed_session,
    consume_session,
    get_monitored_topics,
    get_active_projects
)

class ProactiveEngine:
    def __init__(self, cooldown_seconds: int = 1200): # 20 minute cooldown
        self.cooldown_seconds = cooldown_seconds
        self.last_proactive_time = time.time()
        self.last_focus_area = None

    def get_time_period(self) -> str:
        hour = datetime.datetime.now().hour
        if 6 <= hour < 12:
            return "morning"
        elif 12 <= hour < 18:
            return "afternoon"
        elif 18 <= hour < 23:
            return "evening"
        else:
            return "night"

    def generate_proactive_prompt(self, last_user_messages: list = None) -> dict | None:

        now = time.time()
        if now - self.last_proactive_time < self.cooldown_seconds:
            return None

        time_period = self.get_time_period()
        focus_options = ["session_summary", "monitored_topics", "active_projects", "greeting"]
        
        # Rotate away from last focus area
        if self.last_focus_area in focus_options:
            focus_options.remove(self.last_focus_area)
            
        chosen_focus = random.choice(focus_options)
        self.last_focus_area = chosen_focus
        self.last_proactive_time = now

        if chosen_focus == "session_summary":
            latest_sess = get_latest_unconsumed_session()
            if latest_sess:
                summary = latest_sess.get("summary", "")
                consume_session(latest_sess["id"])
                return {
                    "focus": "session_summary",
                    "text": f"Good {time_period}, Sir. Yesterday you were working on: '{summary}'. Would you like to resume?"
                }

        if chosen_focus == "monitored_topics":
            topics = get_monitored_topics()
            if topics:
                t = random.choice(topics)
                return {
                    "focus": "monitored_topics",
                    "text": f"Checking in on your monitored topic '{t.get('topic')}'. Would you like me to fetch the latest headlines?"
                }

        if chosen_focus == "active_projects":
            projects = get_active_projects()
            if projects:
                p = random.choice(projects)
                return {
                    "focus": "active_projects",
                    "text": f"How is progress on project '{p}' going today?"
                }

        # Default time-based check-in
        greetings = {
            "morning": "Good morning, Sir. Systems are online and ready for your commands.",
            "afternoon": "Good afternoon, Sir. Standing by if you need assistance with tasks or research.",
            "evening": "Good evening, Sir. Let me know if you would like a summary of today's activities.",
            "night": "Working late tonight, Sir. All systems running at optimal performance."
        }
        return {
            "focus": "greeting",
            "text": greetings.get(time_period, greetings["morning"])
        }

proactive_engine = ProactiveEngine()
