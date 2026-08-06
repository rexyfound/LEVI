import json

from distro import name
from tool_registry import TOOLS
from providers.vision_provider import analyze_image
from model_router import chat_with_router
from tools.files import list_files, read_file, write_file
from tools.terminal import run_terminal
from tools.browser import (
    browser_open,
    browser_snapshot,
    browser_click,
    browser_type,
    browser_type_by_text,
    browser_press,
    browser_observe,
    browser_scroll,
)
from integrations.openclaw_client import search_memory, write_memory
from tools.desktop import (
    launch_app,
    mouse_move,
    mouse_click,
    keyboard_type,
    press_key,
    hotkey,
    screenshot,
    active_window,
)
from tools.desktop import (
    launch_app,
    active_window,
    keyboard_type,
    press_key,
    mouse_move,
    mouse_click,
    screenshot,
    hotkey,
)



def execute_tool(name, arguments):
    if name == "list_files":
        return list_files(arguments.get("path", "."))

    if name == "read_file":
        return read_file(arguments["path"])

    if name == "write_file":
        return write_file(
            arguments["path"],
            arguments["content"],
        )

    if name == "run_terminal":
        return run_terminal(arguments["command"])

    if name == "browser_open":
        return browser_open(arguments["url"])

    if name == "browser_snapshot":
        return browser_snapshot()

    if name == "browser_click":
        index = arguments.get("index")

        if index is None:
                return {
            "success": False,
            "error": "browser_click requires an element index. Use browser_observe first to find the correct element."
        }

        return browser_click(index)

    if name == "browser_type":
        index = arguments.get("index")
        text = arguments.get("text")

        if index is None:
            return {
            "success": False,
            "error": "browser_type requires an element index. Use browser_observe first."
        }

        if text is None:
            return {
            "success": False,
            "error": "browser_type requires text."
        }

        return browser_type(index, text)
    
    if name == "browser_type_by_text":
        return browser_type_by_text(
        arguments["label"],
        arguments["text"]
    )
    if name == "browser_press":
        return browser_press(
        arguments["label"],
        arguments["key"]
    )
    if name == "browser_observe":
        return browser_observe()
    if name == "browser_scroll":
        return browser_scroll(
        arguments.get("direction", "down"),
        arguments.get("amount", 700)
    )
    if name == "memory_search":
        return search_memory(
        query=arguments["query"],
        max_results=arguments.get("max_results", 5)
    )
    if name == "memory_write":

        return write_memory(
        arguments["text"]
    )
    if name == "launch_app":
        return launch_app(arguments["path"])

    if name == "mouse_move":
        return mouse_move(
        arguments["x"],
        arguments["y"]
    )

    if name == "mouse_click":
        return mouse_click(
        arguments.get("button", "left")
    )

    if name == "keyboard_type":
        return keyboard_type(arguments["text"])

    if name == "press_key":
        return press_key(arguments["key"])

    if name == "hotkey":
        return hotkey(*arguments["keys"])

    if name == "screenshot":
        return screenshot(
        arguments.get(
            "path",
            "desktop.png"
        )
    )
    if name == "launch_app":
        return launch_app(arguments["path"])

    if name == "active_window":
        return active_window()

    if name == "keyboard_type":
        return keyboard_type(arguments["text"])

    if name == "press_key":
        return press_key(arguments["key"])

    if name == "mouse_move":
        return mouse_move(
        arguments["x"],
        arguments["y"]
    )

    if name == "mouse_click":
        return mouse_click(
        arguments.get("button", "left")
    )

    if name == "hotkey":
        return hotkey(*arguments["keys"])

    if name == "screenshot":
        return screenshot()
    if name=="vision_analyze":
        screenshot()
        return analyze_image(
        "desktop.png",
        arguments["prompt"]
    )
    if name == "active_window":
        return active_window()
    return {
        "error": f"Unknown tool: {name}"
    }

def build_task_context(user_message):
    return {
        "original_request": user_message,
        "completed_actions": [],
        "current_goal": user_message
    }

def run_agent(user_message):
    task = build_task_context(user_message)
    
    messages = []



    system_prompt = """
You are LEVI, a local desktop AI agent.

You have real tools for files, terminal commands and browser automation.

GENERAL RULES:
- Use tools whenever real system or browser information is required.
- Never invent tool results.
- Never claim an action succeeded unless the tool actually succeeded.
- Keep final responses concise and human-readable.
- Never output raw tool-call JSON to the user.
- Continue working on the ORIGINAL user request after every tool result.
- Only give a final answer when the requested task is actually complete.

FILE RULES:
- Work only inside the allowed workspace.
- If an action requires confirmation, stop and wait for approval.

BROWSER RULES:
- Never assume website structure in advance.
- Open the requested website, then inspect it.
- Use browser_snapshot or browser_observe before interacting.
- Never guess element IDs or indexes.
- Prefer browser_type_by_text for recognizable inputs.
- Use browser_type for indexed inputs.
- Use browser_click for buttons and links.
- Use browser_press when keyboard interaction is appropriate.
- After navigation or major page changes, inspect the page again.
- Dismiss harmless popups when they block the requested task.
- If an element becomes stale or invalid, observe again.
- Never invent page content, URLs, titles, IDs or element positions.
- Tool results are observations, not new user messages.
- Do not summarize observations while actions are still required.

BROWSER AUTONOMY RULES:
1. You do not know the structure of a website in advance.
2. Use browser_open to navigate to a website.
3. Immediately use browser_observe to understand the current page.
4. browser_observe returns interactive elements with IDs, roles and names.
5. Reason about those elements and choose the appropriate action.
6. Never guess an element ID.
7. After navigation or a major page change, observe the page again.
8. Dismiss harmless popups if they block the requested task.
9. Use browser_type or browser_type_by_text for text fields.
10. Use browser_click for buttons and links.
11. Use browser_press when keyboard interaction is appropriate.
12. Continue observe -> reason -> act -> observe until the original task is complete.
13. Do not explain raw browser observations to the user.
14. Never assume a website is Amazon, Google, Instagram, or any other specific website.
15. Never claim an interaction succeeded unless its tool result confirms success.
16. Before calling browser_click or browser_type with an index, you MUST use
    browser_observe and select a valid element ID from its latest result.
17. If a browser tool returns an error because an element ID is missing,
    stale, invalid, or unavailable, call browser_observe again and retry
    with a valid element.
18. Never call browser_click without an index.
19. Never invent element indexes.
20. Use browser_scroll when relevant content is outside the current viewport.
21. Never use run_terminal to simulate scrolling, clicking, typing,
    navigation, or any other browser interaction.
22. After scrolling, call browser_observe again before choosing another
    browser action.
23. Scrolling and observing are read-only browser actions and do not require
    user confirmation.
24. If the requested information is not currently visible, continue using
    browser_observe and browser_scroll when appropriate instead of giving up.
25. Stop browsing once the original user request has been completed.
26. Do not perform extra actions that were not requested by the user.
27. Actions with external consequences such as purchases, sending messages,
    submitting forms, deleting data, changing account settings, or publishing
    content must respect the confirmation system.

TASK PLANNING RULES:
1. Always remember the ORIGINAL user request.
2. Before acting, determine the next necessary action toward completing it.
3. Break multi-step tasks into small actions internally.
4. Execute only the next necessary action using the available tools.
5. After every tool result, reassess what remains to be completed.
6. Do not restart the task unless necessary.
7. Do not repeat an action that has already succeeded.
8. Do not stop merely because one intermediate step succeeded.
9. Continue until every required part of the original request is complete.
10. If the task cannot be completed with available tools, clearly state the
    missing capability instead of inventing success.
11. Do not perform unnecessary actions outside the user's request.
12. Once the task is complete, stop using tools and provide a concise result.    

MEMORY RULES:
1. You have access to persistent long-term memory through memory_search.
2. Use memory_search when the user asks about information from a previous
   conversation, past decision, preference, project detail, configuration,
   setting, or anything that may have been remembered earlier.
3. Never invent remembered information.
4. If memory_search returns no relevant result, clearly say that you could
   not find the information in memory.
5. Treat memory_search results as past context, not as new user messages.
6. Do not use memory_search for information already clearly available in
   the current conversation.

MEMORY WRITE RULES

Use memory_write only when the user:

• says remember this
• says save this
• says don't forget
• gives long-term preferences
• gives project settings
• gives API endpoints
• gives passwords? NEVER
• gives secrets? NEVER
• gives temporary information? NEVER

Do not store trivial conversation.

MEMORY RULES

If the user shares information that is likely to be useful in future conversations,
call memory_write.

Examples:
- User preferences
- Project names
- Folder locations
- Long-term goals
- Important recurring information

Never store:
- Passwords
- API keys
- OTPs
- Temporary information
- Sensitive personal information
- Random conversation

TASK COMPLETION RULES

Your goal is to complete the user's request using the minimum number of tools.

After every tool result, ask yourself:

1. Has the user's request already been completed?
2. Do I already have enough information to answer?
3. Would another tool improve the answer?

If the task is complete:

- Stop calling tools immediately.
- Return the final answer.
- Do not verify the same action multiple times.
- Never repeat a tool unless the previous attempt failed.

Never call tools just because they are available.

A successful tool result is usually sufficient to finish the task.

DO NOT LOOP

Never call the same tool repeatedly unless:

- the previous call failed
- the user explicitly asked you to retry
- additional information is required

Otherwise, finish immediately.

STOP CONDITION

Immediately stop tool execution when:

- the requested application has been opened
- the requested file has been written
- the requested browser action has completed
- the requested memory has been stored
- the requested information has been found

Return the final response instead of continuing.

DESKTOP OBSERVATION RULES

When the user asks:

- what is on my screen
- what is open
- what is running visually
- describe my desktop
- what do you see

Never use terminal commands.

Instead:

1. Take a screenshot.
2. Analyze the screenshot with vision.
3. Answer using the screenshot.

Use terminal only when the user explicitly asks for process information.

=========================
TOOL SELECTION RULES
=========================

Always choose the most specialized tool.

Browser tasks
→ browser_* tools

Desktop GUI tasks
→ desktop_* tools

Typing and keyboard
→ keyboard_type, press_key, hotkey

Mouse actions
→ mouse_move, mouse_click

Taking screenshots
→ screenshot

Screen understanding
→ vision_analyze

Remembering information
→ memory_write

Recalling information
→ memory_search

Reading and writing files
→ read_file, write_file

Listing directories
→ list_files

Use run_terminal ONLY if no other tool can accomplish the task.

Never use run_terminal for:

- opening applications
- describing the desktop
- clicking buttons
- reading webpages
- browser automation
- screenshots
- GUI automation
- memory retrieval
"""

    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": user_message
        }
    ]

    max_steps = 6

    browser_actions = []

    browser_task = any(
        word in user_message.lower()
        for word in [
            "browser",
            "click",
            "type",
            "search",
            "website",
            "http://",
            "https://",
            "open"
        ]
    )

    active_provider = None

    for step in range(max_steps):
        print(f"[LEVI] Agent step {step + 1}/{max_steps}")

        # Keep the same provider for the whole multi-step task when possible.
        response, used_provider = chat_with_router(
            messages,
            TOOLS,
            preferred_provider=active_provider,
        )

        if active_provider != used_provider:
         if active_provider is not None:
             print(
            f"[LEVI] Provider switched: "
            f"{active_provider} -> {used_provider}"
        )

        active_provider = used_provider

        print(f"[LEVI] Active provider: {active_provider}")

        # Assistant tool-call messages must be kept in history because the
        # following tool result refers to their tool_call_id.
        messages.append(response)

        tool_calls = response.get("tool_calls") or []
        if not tool_calls:
                print("[LEVI] Task complete.")
                break
        # -----------------------------
        # No tool call
        # -----------------------------
        if not tool_calls:
            content = (response.get("content") or "").strip()

            if browser_task and not browser_actions:
                messages.append({
                    "role": "user",
                    "content": (
                        "The ORIGINAL browser task has not been performed yet. "
                        "Use the appropriate browser tools now. "
                        "Do not merely describe the page."
                    ),
                })
                continue

            if content:
                return {
                    "status": "complete",
                    "response": content,
                }

            messages.append({
                "role": "user",
                "content": (
                    "Continue the ORIGINAL user request. "
                    "Your previous response contained no final answer and no "
                    "tool call. Use another tool if required."
                ),
            })
            continue

        # -----------------------------
        # Execute every tool call
        # -----------------------------
        for call in tool_calls:
            function = call.get("function") or {}
            name = function.get("name")
            arguments = function.get("arguments", {})

            if not name:
                messages.append({
                    "role": "tool",
                    "tool_call_id": call.get("id", "unknown"),
                    "content": json.dumps({
                        "error": "Tool call did not contain a function name."
                    }),
                })
                continue

            if isinstance(arguments, str):
                try:
                    arguments = json.loads(arguments)
                except json.JSONDecodeError as exc:
                    arguments = {
                        "_argument_parse_error": str(exc),
                        "_raw_arguments": arguments,
                    }

            if not isinstance(arguments, dict):
                arguments = {"value": arguments}

            print(f"[LEVI] Tool: {name}")

            if "_argument_parse_error" in arguments:
                result = {
                    "error": "Invalid JSON tool arguments.",
                    "details": arguments["_argument_parse_error"],
                }
            else:
                try:
                    result = execute_tool(name, arguments)
                except Exception as exc:
                    result = {
                        "error": f"{type(exc).__name__}: {exc}"
                    }

            if not isinstance(result, dict):
                result = {"result": result}

            # -----------------------------
            # Approval
            # -----------------------------
            if result.get("requires_confirmation"):
                return {
                    "status": "awaiting_confirmation",
                    "response": "This action requires your approval.",
                    "pending_action": result,
                }

            # -----------------------------
            # Track successful actions
            # -----------------------------
            if not result.get("error"):
                task["completed_actions"].append({
                    "tool": name,
                    "arguments": arguments,
                })

            if name.startswith("browser_"):
                browser_actions.append({
                    "tool": name,
                    "arguments": arguments,
                    "result": result,
                })

            # -----------------------------
            # Return tool result to model
            # -----------------------------
            tool_content = json.dumps(result, ensure_ascii=False)

            if len(tool_content) > 6000:
                tool_content = tool_content[:6000] + "...[truncated]"

            messages.append({
                "role": "tool",
                "tool_call_id": call.get("id", "unknown"),
                "content": tool_content,
            })

    return {
        "status": "stopped",
        "response": "Maximum agent steps reached.",
    }
def create_plan(user_message: str):

    return f"""
You are LEVI Planner.

Break the user's goal into the smallest possible executable steps.

Rules:
- Return ONLY JSON.
- Each step should require one tool or one reasoning action.
- Don't execute anything.
- Don't explain.

Example:

{{
  "steps":[
    "Open browser",
    "Search OpenClaw",
    "Clone repository"
  ]
}}

User:

{user_message}
"""
