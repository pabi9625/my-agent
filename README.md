# My Agent

A simple terminal AI agent built in Python from scratch for learning purposes. It uses the **DeepSeek API** (OpenAI-compatible) with **tool calling**, so the model can decide when to use Python functions such as reading files, doing math, or checking the time.

No agent frameworks are used. The goal is to understand how an agent works underneath.

---

## Features

- 💬 Interactive chat in the terminal with conversation memory
- 🛠️ Tool calling: the model picks and runs tools on its own
- 🔁 Multi-step reasoning: chains several tools to complete one request
- ⚠️ Permission prompt before risky actions (writing files)
- 🛑 Step limit to prevent infinite loops
- 🧯 Error handling for API failures and bad tool arguments

### Available tools

| Tool | What it does |
|------|--------------|
| `get_time` | Returns the current date and time |
| `calculator` | Evaluates a math expression |
| `list_files` | Lists files in a folder |
| `read_file` | Reads a text file (first 5000 characters) |
| `write_file` | Creates or overwrites a text file (asks for permission) |

---

## How it works

```
You type a message
   ↓
Conversation + tool list are sent to the model
   ↓
Did the model ask to use a tool?
   ├─ YES → Python runs the tool → result is sent back → ask the model again
   └─ NO  → print the final answer → wait for your next message
```

- The model **never runs code itself**. It only requests a tool by name with arguments.
- Python executes the tool and returns the result as a `tool` message.
- "Memory" is a list of messages that is resent with every request.

The code has two loops:

- **Outer loop**: the conversation between you and the agent
- **Inner loop**: the agent loop, model → tool → model, until a final answer or the step limit

---

## Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (Python package and project manager)
- A DeepSeek API key from [platform.deepseek.com](https://platform.deepseek.com/api_keys)

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/my-agent.git
cd my-agent
```

### 2. Install dependencies

```bash
uv sync
```

This creates a `.venv` folder and installs `openai` and `python-dotenv`.

### 3. Add your API key

Create a file named `.env` in the project root:

```
DEEPSEEK_API_KEY=sk-your-key-here
```

> ⚠️ Never commit `.env`. It is listed in `.gitignore`.
> On Windows, create this file in VS Code rather than with `echo` in PowerShell, which saves it in an encoding `python-dotenv` cannot read.

### 4. Run

```bash
uv run agent.py
```

Type `exit` or `quit` to stop.

---

## Example prompts

```
What time is it?
What is (345 * 12) / 7?
What files are here? Summarize agent.py
Create notes.txt with 3 Python tips
```

Example output:

```
You: What files are here? Summarize agent.py
  [step 1] tool: list_files({})
  [result] .env
.gitignore
agent.py
pyproject.toml
...
  [step 2] tool: read_file({'path': 'agent.py'})
  [result] """
Simple AI Agent (learning project)
...

AI: The folder contains ... agent.py is a terminal AI agent that ...
```

---

## Project structure

```
my-agent/
├── .env              # API key (not committed)
├── .gitignore
├── .python-version
├── pyproject.toml    # project info and dependencies
├── uv.lock           # exact dependency versions
├── agent.py          # the agent: client, tools, schemas, loops
└── README.md
```

---

## Adding a new tool

Each tool needs three things:

1. **A Python function** that returns a string
   ```python
   def get_weather(city):
       return f"It is sunny in {city}"
   ```
2. **A schema** added to `TOOLS` so the model knows it exists
   ```python
   {
       "type": "function",
       "function": {
           "name": "get_weather",
           "description": "Get the weather for a city",
           "parameters": {
               "type": "object",
               "properties": {"city": {"type": "string"}},
               "required": ["city"],
           },
       },
   }
   ```
3. **An entry** in `TOOL_FUNCTIONS`
   ```python
   "get_weather": get_weather,
   ```

To require permission before it runs, add its name to `DANGEROUS_TOOLS`.

---

## Configuration

Settings at the top of `agent.py`:

| Setting | Default | Purpose |
|---------|---------|---------|
| `MODEL` | `deepseek-flash` | DeepSeek model name |
| `MAX_STEPS` | `10` | Max tool rounds per message |
| `DANGEROUS_TOOLS` | `{"write_file"}` | Tools that need y/n approval |

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `Missing DEEPSEEK_API_KEY` | Check that `.env` exists in the project root and is spelled correctly |
| `401 Authentication error` | API key is wrong or `.env` was saved in the wrong encoding |
| `402 Insufficient Balance` | Top up your DeepSeek account |
| `ModuleNotFoundError` | Run with `uv run agent.py`, not plain `python` |
| `uv` not recognized | Reopen the terminal after installing uv, or add it to PATH |

---

## Limitations

- `calculator` uses `eval`, which is fine for learning but unsafe in production
- `read_file` only returns the first 5000 characters
- Conversation history grows with every message and is lost when the program exits
- No streaming: replies appear all at once

## Ideas for next steps

- Split tools into a separate `tools.py`
- Add a web search tool
- Stream responses word by word
- Save conversation history to a file
- Replace `eval` with a safe math parser

---

## What I learned

- How LLM chat APIs work (`messages`, roles, stateless requests)
- How tool / function calling works with JSON Schema
- How an agent loop decides between calling tools and giving a final answer
- Basic agent safety: step limits and human approval for risky actions
- Managing Python projects with `uv`