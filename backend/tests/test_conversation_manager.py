from conversation_manager import ConversationManager


def test_session_context_is_isolated_and_includes_verified_paths():
    manager = ConversationManager()
    manager.add_turn(
        "session-a",
        "Create a calculator",
        "Created it.",
        [{"tool": "write_file", "result": {"path": "C:/Users/test/Documents/calculator.py"}}],
    )
    context = manager.context_for("session-a")
    assert "calculator.py" in context
    assert manager.context_for("session-b") == ""
