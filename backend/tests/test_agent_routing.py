import json

from agent_roles import classify_task
from tool_registry import RESEARCH_TOOLS
from voice.text_shortener import prepare_spoken_text
from providers.anthropic_provider import _from_anthropic, _to_anthropic_messages, _to_anthropic_tools


def test_task_roles_prioritize_coding_and_design():
    assert classify_task("debug the Python API and add tests").name == "coding"
    assert classify_task("create a visual UI mockup").name == "design"
    assert classify_task("what is the latest news?").name == "research"
    assert classify_task("open the browser and click the button").name == "automation"
    assert classify_task("remember my coffee preference").name == "general"


def test_research_requests_use_research_mode_and_actions_override():
    keyboard = classify_task("find me a keyboard with my specifications")
    assert keyboard.name == "research"
    assert keyboard.execution_mode == "research"
    assert keyboard.max_steps == 3

    assert classify_task("recommend the best laptop for coding").execution_mode == "research"
    assert classify_task("search for a quiet mechanical keyboard").execution_mode == "research"

    action = classify_task("open the browser and find a keyboard")
    assert action.name == "automation"
    assert action.execution_mode == "action"


def test_research_tool_allowlist_excludes_local_control():
    names = {tool["function"]["name"] for tool in RESEARCH_TOOLS}
    assert names == {"parallel_web_search", "memory_search", "memory_write"}
    assert not any(name.startswith("browser_") for name in names)
    assert "keyboard_type" not in names


def test_visible_response_cleanup_removes_markdown_artifacts():
    raw = '### Top Recommendation: **EvoFox Ronin X75**\\n* **Mounting:** True gasket mount.'
    clean = prepare_spoken_text(raw, max_chars=800)
    assert clean == 'Top Recommendation: EvoFox Ronin X75 Mounting: True gasket mount.'
    assert '**' not in clean
    assert '###' not in clean


def test_anthropic_conversion_preserves_tools_and_results():
    messages = [
        {"role": "system", "content": "You are LEVI."},
        {"role": "user", "content": "Read the file."},
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": "call_1",
                    "function": {"name": "read_file", "arguments": json.dumps({"path": "README.MD"})},
                }
            ],
        },
        {"role": "tool", "tool_call_id": "call_1", "content": "hello"},
    ]
    system, converted = _to_anthropic_messages(messages)
    assert system == "You are LEVI."
    assert converted[1]["content"][0]["type"] == "tool_use"
    assert converted[2]["content"][0]["type"] == "tool_result"

    tools = _to_anthropic_tools([
        {"type": "function", "function": {"name": "read_file", "parameters": {"type": "object"}}}
    ])
    assert tools[0]["input_schema"]["type"] == "object"

    response = _from_anthropic({
        "content": [
            {"type": "text", "text": "I will read it."},
            {"type": "tool_use", "id": "call_1", "name": "read_file", "input": {"path": "README.MD"}},
        ]
    })
    assert response["content"] == "I will read it."
    assert response["tool_calls"][0]["function"]["name"] == "read_file"
