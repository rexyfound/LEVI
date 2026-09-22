import subprocess
import re

def get_clipboard_text() -> str:
    try:
        res = subprocess.run(
            ["powershell", "-Command", "Get-Clipboard"],
            capture_output=True,
            text=True,
            timeout=5
        )
        return res.stdout.strip()
    except Exception:
        return ""

def analyze_clipboard() -> dict:
    """
    Read and intelligently classify the current Windows clipboard content.
    """
    text = get_clipboard_text()
    if not text:
        return {"success": False, "message": "Clipboard is empty or contains non-text data."}

    # Intelligent Classification
    category = "PLAIN_TEXT"
    summary = text[:120] + ("..." if len(text) > 120 else "")

    if re.match(r"^https?://[^\s]+$", text):
        category = "URL"
    elif any(kw in text for kw in ["Traceback (most recent call last):", "Exception:", "Error:", "NullPointerException", "TypeError"]):
        category = "ERROR_TRACEBACK"
    elif any(kw in text for kw in ["def ", "function ", "import ", "const ", "class ", "return ", "if __name__"]):
        category = "CODE_SNIPPET"

    return {
        "success": True,
        "category": category,
        "length": len(text),
        "summary": summary,
        "content": text
    }
