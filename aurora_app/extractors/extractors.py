from typing import Any, Dict, List


def build_documents(messages: List[Dict[str, Any]]) -> List[str]:
    """
    Convert each raw message dict into a plain-text document string.

    Focus on the key fields that will help the QA system:
    - user_name / member_name
    - timestamp
    - message text
    - ids as backup context
    """
    docs: List[str] = []

    for msg in messages:
        if not isinstance(msg, dict):
            docs.append(str(msg))
            continue

        parts: List[str] = []

        # Try different name fields
        name = (
            msg.get("user_name")
            or msg.get("member_name")
            or msg.get("name")
        )
        if name:
            parts.append(f"User: {name}")

        if "timestamp" in msg:
            parts.append(f"Timestamp: {msg['timestamp']}")

        if "message" in msg:
            parts.append(f"Message: {msg['message']}")

        # IDs for reference, not strictly needed but can help context
        if "id" in msg:
            parts.append(f"id: {msg['id']}")
        if "user_id" in msg:
            parts.append(f"user_id: {msg['user_id']}")
        if "member_id" in msg:
            parts.append(f"member_id: {msg['member_id']}")

        # Fallback: if we somehow didn't add anything, just stringify the dict
        if not parts:
            docs.append(str(msg))
        else:
            docs.append(" | ".join(parts))

    return docs
