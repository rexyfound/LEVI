import time
import uuid
import subprocess

pending_actions = {}
ACTION_TTL_SECONDS = 600

def _cleanup_expired():
    """Remove entries older than ACTION_TTL_SECONDS."""
    now = time.time()
    expired = [
        aid for aid, action in pending_actions.items()
        if now - action.get("created_at", 0) > ACTION_TTL_SECONDS
    ]
    for aid in expired:
        pending_actions.pop(aid, None)

def create_pending_action(action_type, data):
    _cleanup_expired()
    action_id = str(uuid.uuid4())
    pending_actions[action_id] = {
        "action_id": action_id,
        "type": action_type,
        "data": data,
        "created_at": time.time(),
    }
    return action_id

def get_pending_action(action_id):
    action = pending_actions.get(action_id)
    if action is None:
        return None
    if time.time() - action.get("created_at", 0) > ACTION_TTL_SECONDS:
        pending_actions.pop(action_id, None)
        return None
    return action

def get_latest_pending_action():
    _cleanup_expired()
    if not pending_actions:
        return None
    # Sort by created_at descending
    sorted_actions = sorted(pending_actions.values(), key=lambda x: x.get("created_at", 0), reverse=True)
    return sorted_actions[0]

def remove_pending_action(action_id):
    return pending_actions.pop(action_id, None)

def execute_pending_action(action_id: str, approved: bool) -> dict:
    action = get_pending_action(action_id)
    if not action:
        return {"success": False, "error": "Action not found or expired"}

    if not approved:
        remove_pending_action(action_id)
        return {"success": True, "status": "denied", "message": "Action execution denied by user."}

    action_type = action.get("type")
    data = action.get("data", {})

    try:
        if action_type == "overwrite_file":
            path = data.get("path")
            content = data.get("content", "")
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            remove_pending_action(action_id)
            return {"success": True, "status": "executed", "action": "overwrite_file", "path": path, "message": f"File '{path}' successfully overwritten."}

        elif action_type == "run_terminal":
            command = data.get("command", "")
            result = subprocess.run(command, shell=True, cwd="D:/Projects", capture_output=True, text=True, timeout=30)
            remove_pending_action(action_id)
            return {
                "success": True,
                "status": "executed",
                "action": "run_terminal",
                "command": command,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode,
                "message": f"Terminal command '{command}' executed successfully."
            }

        elif action_type == "launch_app":
            path = data.get("path", "")
            subprocess.Popen(path)
            remove_pending_action(action_id)
            return {"success": True, "status": "executed", "action": "launch_app", "path": path, "message": f"Application '{path}' launched."}

        else:
            remove_pending_action(action_id)
            return {"success": False, "error": f"Unknown action type: {action_type}"}

    except Exception as e:
        return {"success": False, "error": str(e)}