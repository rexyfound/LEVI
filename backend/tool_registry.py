TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
                    "description": "List files and directories inside D:/Projects or the user's Documents folder.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path inside D:/Projects or the user's Documents folder",
                    }
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
                    "description": "Read a text file inside D:/Projects or the user's Documents folder.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "File path inside D:/Projects or the user's Documents folder",
                    }
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
                    "description": "Create or modify a text file inside D:/Projects or the user's Documents folder.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "File path inside D:/Projects or the user's Documents folder",
                    },
                    "content": {
                        "type": "string",
                        "description": "Complete content to write to the file",
                    },
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_terminal",
            "description": (
            "Execute a shell command only when terminal access is absolutely required. "
            "Use this tool for package installation, git, scripting, system information, "
            "or file operations that cannot be done with other tools. "
            "Do NOT use this tool for browser interaction, desktop observation, "
            "GUI automation, screenshots, or memory operations. "
            "Prefer browser tools, desktop tools, memory tools, and file tools whenever possible."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                    }
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "browser_open",
            "description": "Open a URL in the persistent Chromium browser.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                    }
                },
                "required": ["url"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "browser_snapshot",
            "description": (
                "Inspect the current browser page and return visible "
                "interactive elements with their indexes."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "browser_click",
            "description": (
                "Click an interactive browser element using an index "
                "returned by browser_snapshot."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "index": {
                        "type": "integer",
                    }
                },
                "required": ["index"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "browser_type",
            "description": (
                "Type text into an input using an index returned "
                "by browser_snapshot."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "index": {
                        "type": "integer",
                    },
                    "text": {
                        "type": "string",
                    },
                },
                "required": ["index", "text"],
            },
        },
    },
    {
    "type": "function",
    "function": {
        "name": "browser_type_by_text",
        "description": (
            "Find an input using its visible label, placeholder, "
            "or aria-label and type text into it. Prefer this when "
            "the input index is unknown."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "label": {
                    "type": "string"
                },
                "text": {
                    "type": "string"
                }
            },
            "required": ["label", "text"]
        }
    }
}, {
    "type": "function",
    "function": {
        "name": "browser_press",
        "description": (
            "Press a key on an element using its visible label, placeholder, "
            "or aria-label. Prefer this when the element index is unknown."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "label": {
                    "type": "string"
                },
                "key": {
                    "type": "string"
                }
            },
            "required": ["label", "key"]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "browser_observe",
        "description": (
            "Observe the current webpage and return a compact list "
            "of visible interactive elements such as buttons, links, "
            "textboxes and dropdowns. Use this to understand an "
            "unknown website before interacting with it."
        ),
        "parameters": {
            "type": "object",
            "properties": {}
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "browser_scroll",
        "description": "Scroll the current browser page up or down.",
        "parameters": {
            "type": "object",
            "properties": {
                "direction": {
                    "type": "string",
                    "enum": ["up", "down"]
                },
                "amount": {
                    "type": "integer",
                    "description": "Approximate number of pixels to scroll."
                }
            },
            "required": ["direction"]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "memory_search",
        "description": (
            "Search LEVI persistent long-term memory for previously "
            "stored information, user preferences, project details, "
            "past decisions, settings, and other remembered facts. "
            "Use this when the user refers to something from the past "
            "or asks LEVI to recall previously known information."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "A concise semantic search query describing "
                        "the information that needs to be recalled."
                    )
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum memory results to retrieve.",
                    "default": 5
                }
            },
            "required": ["query"]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "memory_write",
        "description": (
            "Store important long-term information about the user, "
            "their preferences, projects, goals, settings, or facts "
            "that should be remembered across future conversations. "
            "Never store passwords, API keys, OTPs, or other secrets."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": (
                        "A concise factual memory to store."
                    )
                }
            },
            "required": [
                "text"
            ]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "launch_app",
        "description": "Launch a Windows application.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Application name or executable path."
                }
            },
            "required": ["path"]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "active_window",
        "description": "Get the currently focused desktop window.",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "keyboard_type",
        "description": "Type text into the active desktop application.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string"
                }
            },
            "required": ["text"]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "press_key",
        "description": "Press a keyboard key.",
        "parameters": {
            "type": "object",
            "properties": {
                "key": {
                    "type": "string"
                }
            },
            "required": ["key"]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "mouse_move",
        "description": "Move the mouse cursor.",
        "parameters": {
            "type": "object",
            "properties": {
                "x": {
                    "type": "integer"
                },
                "y": {
                    "type": "integer"
                }
            },
            "required": ["x", "y"]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "mouse_click",
        "description": "Click the mouse.",
        "parameters": {
            "type": "object",
            "properties": {
                "button": {
                    "type": "string",
                    "enum": [
                        "left",
                        "right",
                        "middle"
                    ]
                }
            }
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "hotkey",
        "description": "Press multiple keyboard keys together.",
        "parameters": {
            "type": "object",
            "properties": {
                "keys": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                }
            },
            "required": ["keys"]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "screenshot",
        "description": "Capture a desktop screenshot.",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "vision_analyze",
        "description": "Analyze the current desktop screenshot.",
        "parameters": {
            "type": "object",
            "properties": {
                "prompt": {
                    "type": "string"
                }
            },
            "required": ["prompt"]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "set_master_volume",
        "description": "Set system master volume percentage (0 to 100).",
        "parameters": {
            "type": "object",
            "properties": {
                "level": {
                    "type": "integer",
                    "description": "Volume percentage from 0 to 100"
                }
            },
            "required": ["level"]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "mute_volume",
        "description": "Mute or toggle audio output.",
        "parameters": {
            "type": "object",
            "properties": {
                "mute": {
                    "type": "boolean",
                    "description": "True to mute, False to unmute"
                }
            }
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "set_screen_brightness",
        "description": "Set display brightness percentage (0 to 100).",
        "parameters": {
            "type": "object",
            "properties": {
                "level": {
                    "type": "integer",
                    "description": "Brightness percentage from 0 to 100"
                }
            },
            "required": ["level"]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "system_power_action",
        "description": "Execute system power commands like lock or sleep.",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["lock", "sleep"],
                    "description": "Power action: 'lock' or 'sleep'"
                }
            },
            "required": ["action"]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "media_control",
        "description": "Control media playback (play_pause, next, prev, stop).",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "enum": ["play_pause", "next", "prev", "stop"],
                    "description": "Media command"
                }
            },
            "required": ["command"]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "parallel_web_search",
        "description": "Perform fast multi-threaded search across DuckDuckGo and Wikipedia.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query"
                }
            },
            "required": ["query"]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "monitor_topic",
        "description": "Add a topic for LEVI to monitor daily in the background. (Crypto and trading topics are blocked).",
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "Topic or keyword to monitor"
                }
            },
            "required": ["topic"]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "unmonitor_topic",
        "description": "Stop monitoring a previously added topic.",
        "parameters": {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "Topic to remove"
                }
            },
            "required": ["topic"]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "list_monitored_topics",
        "description": "List all currently monitored topics.",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "set_autostart",
        "description": "Enable or disable LEVI auto-starting on Windows startup.",
        "parameters": {
            "type": "object",
            "properties": {
                "enable": {
                    "type": "boolean",
                    "description": "True to enable Windows startup auto-start, False to disable"
                }
            },
            "required": ["enable"]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "get_autostart_status",
        "description": "Check if Windows auto-start is currently enabled.",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "analyze_clipboard",
        "description": "Read and classify the current Windows clipboard content (URL, Code Snippet, Error Traceback, Text).",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "update_assistant_config",
        "description": "Customize assistant name (e.g. LEVI, JARVIS, MARK L), user name, voice profile, or personality rules.",
        "parameters": {
            "type": "object",
            "properties": {
                "assistant_name": { "type": "string" },
                "user_name": { "type": "string" },
                "personality_rules": { "type": "string" },
                "voice_profile": { "type": "string" }
            }
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "get_assistant_config",
        "description": "Get current assistant name, user name, and customization profile.",
        "parameters": {
            "type": "object",
            "properties": {}
        }
        }
}
]


# Tool allowlists keep AI-side research separate from explicit local computer
# actions. MCP tools are intentionally excluded from research mode as well.
RESEARCH_TOOL_NAMES = {"parallel_web_search", "memory_search", "memory_write"}
RESEARCH_TOOLS = [
    tool for tool in TOOLS
    if tool.get("function", {}).get("name") in RESEARCH_TOOL_NAMES
]
ACTION_TOOLS = TOOLS
