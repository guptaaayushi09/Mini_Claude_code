# Mini Claude Code

A minimal, from-scratch clone of an agentic coding assistant, built to understand how tool-calling, function execution, and multi-turn conversation loops work under the hood using the OpenAI API.

## What it does

This is a command-line chat assistant that can reason about your local file system and take real actions on it — reading files, writing files, listing directories, and running shell commands — all driven by natural language requests.

## Features / Tools

| Tool | Description |
|---|---|
| `read_json_file` | Reads and parses a JSON file from disk. |
| `create_file` | Creates a new file with optional content. Fails if the file already exists. |
| `write_file` | Writes content to a file, overwriting it if it exists. |
| `list_files` | Lists files and folders in a given directory (defaults to current directory). |
| `run_command` | Executes a shell command and returns its output. Requires manual confirmation before running. |

## How it works

1. The user's message is sent to the model along with a list of available tool schemas.
2. If the model decides a tool is needed, it responds with a tool call instead of plain text.
3. The corresponding Python function is executed locally, and its result is sent back to the model as a `tool` role message.
4. The model uses that result to generate a final natural-language response.

This mirrors the core loop used by real coding agents: **reason → call a tool → observe the result → respond**.

## Setup

```bash
# Clone the repo
git clone https://github.com/guptaaayushi09/mini-claude-code.git
cd mini-claude-code

# Install dependencies with uv
uv sync
```

Set your OpenAI API key as an environment variable (never hardcode it in source):

```bash
export OPENAI_API_KEY="your-api-key-here"
```

## Usage

```bash
uv run main.py
```

Then chat with it directly.