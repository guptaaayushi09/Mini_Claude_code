import os
import json
import subprocess
from openai import OpenAI

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
MODEL = "gpt-5-mini"

SYSTEM_PROMPT = (
    "You are a helpful coding assistant that can read, write, and create files, "
    "list directory contents, and run shell commands on the local file system."
)

# ---------- Tool implementations ----------

def read_json_file(file_path):
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except Exception as e:
        raise Exception(f"Error reading JSON file: {e}")

def create_file(file_path, content=""):
    if os.path.exists(file_path):
        raise Exception(f"File '{file_path}' already exists. Use write_file to overwrite it.")
    with open(file_path, 'w') as file:
        file.write(content)
    return f"File '{file_path}' created successfully."

def write_file(file_path, content):
    with open(file_path, 'w') as file:
        file.write(content)
    return f"File '{file_path}' written successfully ({len(content)} chars)."

def list_files(directory_path="."):
    if not os.path.isdir(directory_path):
        raise Exception(f"'{directory_path}' is not a valid directory.")
    entries = os.listdir(directory_path)
    return entries

def run_command(command):
    # Safety gate: ask for human confirmation before executing anything
    confirm = input(f"\n⚠️  Model wants to run: `{command}`\nAllow? (y/n): ").strip().lower()
    if confirm != "y":
        return "Command execution denied by user."
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True, timeout=30
        )
        output = result.stdout.strip()
        error = result.stderr.strip()
        if result.returncode != 0:
            return f"Command failed (exit code {result.returncode}).\nSTDOUT: {output}\nSTDERR: {error}"
        return output if output else "Command ran successfully with no output."
    except subprocess.TimeoutExpired:
        return "Command timed out after 30 seconds."
    except Exception as e:
        return f"Error running command: {e}"

# ---------- Tool schemas ----------

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "read_json_file",
            "description": "Reads a JSON file and returns its content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "The path to the JSON file."}
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_file",
            "description": "Creates a new file with optional content. Fails if the file already exists.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path of the file to create."},
                    "content": {"type": "string", "description": "Initial content of the file."}
                },
                "required": ["file_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Writes content to a file, overwriting it if it already exists.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path of the file to write."},
                    "content": {"type": "string", "description": "Content to write into the file."}
                },
                "required": ["file_path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "Lists files and folders inside a given directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "directory_path": {"type": "string", "description": "Directory to list. Defaults to current directory."}
                },
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Runs a shell command and returns its output. Requires user confirmation before execution.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The shell command to execute."}
                },
                "required": ["command"]
            }
        }
    }
]

# ---------- Dispatch table ----------

def dispatch_tool_call(name, args):
    if name == "read_json_file":
        return json.dumps(read_json_file(args["file_path"]))
    elif name == "create_file":
        return create_file(args["file_path"], args.get("content", ""))
    elif name == "write_file":
        return write_file(args["file_path"], args["content"])
    elif name == "list_files":
        return json.dumps(list_files(args.get("directory_path", ".")))
    elif name == "run_command":
        return run_command(args["command"])
    else:
        return f"Unknown tool: {name}"

# ---------- Main chat loop ----------

messages = [{"role": "system", "content": SYSTEM_PROMPT}]

while True:
    user_input = input("You: ")
    if user_input.strip().lower() in ("exit", "quit"):
        print("Exiting the chat. Take care!")
        break

    messages.append({"role": "user", "content": user_input})

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        tools=TOOL_SCHEMAS,
    )

    reply = response.choices[0].message
    assistant_message = {"role": "assistant", "content": reply.content}
    if reply.tool_calls:
        assistant_message["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {"name": tc.function.name, "arguments": tc.function.arguments},
            }
            for tc in reply.tool_calls
        ]
    messages.append(assistant_message)

    if not reply.tool_calls:
        print(f"Assistant: {reply.content}")
        continue

    for tool_call in reply.tool_calls:
        try:
            args = json.loads(tool_call.function.arguments)
            result = dispatch_tool_call(tool_call.function.name, args)
        except Exception as e:
            result = f"Error executing tool '{tool_call.function.name}': {e}"

        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": result,
        })

    followup = client.chat.completions.create(model=MODEL, messages=messages)
    final_reply = followup.choices[0].message
    messages.append({"role": "assistant", "content": final_reply.content})
    print(f"Assistant: {final_reply.content}")