# STEP 1: Imports and API client 
import os
import json
import datetime
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()  # reads DEEPSEEK_API_KEY from .env

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com",
)
MODEL = "deepseek-flash"
MAX_STEPS = 10  # Step 7: safety limit for the agent loop


# STEP 3 + 6: Tools (normal Python functions that return strings) 

def get_time():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def calculator(expression):
    try:
        # eval is unsafe in real apps; fine for learning
        return str(eval(expression, {"__builtins__": {}}))
    except Exception as e:
        return f"Error: {e}"


def list_files(folder="."):
    try:
        return "\n".join(os.listdir(folder))
    except Exception as e:
        return f"Error: {e}"


def read_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()[:5000]  # limit size sent to the model
    except Exception as e:
        return f"Error: {e}"


def write_file(path, content):
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Saved {len(content)} characters to {path}"
    except Exception as e:
        return f"Error: {e}"
        
# STEP 4: Tool schemas (what the model reads)

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_time",
            "description": "Get the current date and time",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "Evaluate a math expression like '12*(3+4)'",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "Math expression"}
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List files and folders in a directory",
            "parameters": {
                "type": "object",
                "properties": {
                    "folder": {"type": "string", "description": "Folder path, default '.'"}
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the text content of a file",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path"}
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Create or overwrite a text file with given content",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path"},
                    "content": {"type": "string", "description": "Text to write"},
                },
                "required": ["path", "content"],
            },
        },
    },
]

# Name the model asks for -> Python function that runs
TOOL_FUNCTIONS = {
    "get_time": get_time,
    "calculator": calculator,
    "list_files": list_files,
    "read_file": read_file,
    "write_file": write_file,
}

# Step 7: tools that need your permission before running
DANGEROUS_TOOLS = {"write_file"}

 
# Helper: run one tool call safely

def run_tool(name, args):
    func = TOOL_FUNCTIONS.get(name)
    if func is None:
        return f"Unknown tool: {name}"

    if name in DANGEROUS_TOOLS:
        answer = input(f"  ⚠ Allow {name}({args})? (y/n): ").strip().lower()
        if answer != "y":
            return "User denied this action"

    try:
        return str(func(**args))
    except TypeError as e:  # wrong/missing arguments from the model
        return f"Bad arguments: {e}"


# STEP 2 + 5: Chat loop (outer) and agent loop (inner)

def main():
    if not os.getenv("DEEPSEEK_API_KEY"):
        print("Missing DEEPSEEK_API_KEY. Check your .env file.")
        return

    messages = [
        {
            "role": "system",
            "content": "You are a helpful agent. Use tools when needed. "
                       "Explain briefly what you did.",
        }
    ]

    print("Agent ready. Type 'exit' to quit.")

    # OUTER LOOP: you <-> agent
    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in ("exit", "quit"):
            break
        if not user_input:
            continue

        messages.append({"role": "user", "content": user_input})

        # INNER LOOP: model <-> tools, until a final answer
        for step in range(MAX_STEPS):
            try:
                response = client.chat.completions.create(
                    model=MODEL,
                    messages=messages,
                    tools=TOOLS,
                )
            except Exception as e:
                print(f"\nAPI error: {e}")
                break

            msg = response.choices[0].message
            messages.append(msg.model_dump(exclude_none=True))  # save assistant turn

            # No tool requested -> final answer
            if not msg.tool_calls:
                print(f"\nAI: {msg.content}")
                break

            # Model requested one or more tools
            for call in msg.tool_calls:
                name = call.function.name
                try:
                    args = json.loads(call.function.arguments or "{}")
                except json.JSONDecodeError:
                    args = {}

                print(f"  [step {step + 1}] tool: {name}({args})")
                result = run_tool(name, args)
                print(f"  [result] {result[:200]}")  # show a preview only

                messages.append({
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": result,
                })
        else:
            print("\nStopped: reached the step limit.")


if __name__ == "__main__":
    main()