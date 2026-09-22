from memory.memory_manager import load_memory, save_memory

def update_assistant_config(
    assistant_name: str = None,
    user_name: str = None,
    personality_rules: str = None,
    voice_profile: str = None
) -> dict:
    """
    Update assistant identity, user name, and personality prompt settings.
    """
    data = load_memory()
    
    if assistant_name:
        data.setdefault("assistant", {})["name"] = assistant_name.strip()
    if user_name:
        data.setdefault("user", {})["name"] = user_name.strip()
    if personality_rules:
        data.setdefault("assistant", {})["personality_rules"] = personality_rules.strip()
    if voice_profile:
        data.setdefault("assistant", {})["voice_profile"] = voice_profile.strip()

    save_memory(data)
    return {
        "success": True,
        "assistant_name": data.get("assistant", {}).get("name", "LEVI"),
        "user_name": data.get("user", {}).get("name", "Sir"),
        "voice_profile": data.get("assistant", {}).get("voice_profile", "Default"),
        "message": "Assistant configuration updated successfully."
    }

def get_assistant_config() -> dict:
    """
    Retrieve current assistant customization profile.
    """
    data = load_memory()
    return {
        "success": True,
        "assistant_name": data.get("assistant", {}).get("name", "LEVI"),
        "user_name": data.get("user", {}).get("name", "Sir"),
        "personality_rules": data.get("assistant", {}).get("personality_rules", ""),
        "voice_profile": data.get("assistant", {}).get("voice_profile", "Default")
    }
