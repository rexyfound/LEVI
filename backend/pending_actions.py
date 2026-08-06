import uuid

pending_actions = {}


def create_pending_action(action_type, data):
    action_id = str(uuid.uuid4())

    pending_actions[action_id] = {
        "type": action_type,
        "data": data
    }

    return action_id


def get_pending_action(action_id):
    return pending_actions.get(action_id)


def remove_pending_action(action_id):
    return pending_actions.pop(action_id, None)