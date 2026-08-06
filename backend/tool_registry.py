TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files and directories inside the D:/Projects workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path inside D:/Projects",
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
            "description": "Read a text file inside the D:/Projects workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative file path inside D:/Projects",
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
            "description": "Create or modify a text file inside the D:/Projects workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative file path inside D:/Projects",
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
    "type":"function",
    "function":{
        "name":"vision_analyze",
        "description":"Analyze the current desktop screenshot.",
        "parameters":{
            "type":"object",
            "properties":{
                "prompt":{
                    "type":"string"
                }
            },
            "required":["prompt"]
        }
    }
},
]