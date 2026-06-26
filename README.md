# Terminal Pilot

A minimalist, interactive CLI tool to connect to OpenRouter and chat with free AI models directly from your terminal.

## Installation

You can install Terminal Pilot globally directly from PyPI:
```bash
pip install Terminal-Pilot
```

## Configuration

You need an OpenRouter API key to use this tool. 
Create a file named `.env` in this directory (or in your home directory as `.terminal_pilot_env`) and add your key:

```env
OPENROUTER_API_KEY=your_openrouter_key_here
```

## Usage

Start the interactive assistant from anywhere in your terminal:

```bash
tp start
```

Inside the interactive chat, you can instantly load files into the AI's memory by using the `/read` command:
```text
? You: /read requirements.md
✓ Loaded requirements.md into memory!
? You: Give me a summary of this project.
```

### Changing Models Mid-Chat
If a model hits a rate limit or you want to switch to a different one, you don't need to exit. Just type `/model` to hot-swap:
```text
? You: /model
✓ Switched model to: google/gemma-3
```

### Pipe Support (stdin)
You can pipe data directly into the AI to analyze logs, code, or command outputs instantly without opening an interactive chat:

```bash
cat error.log | tp ask "Why is this crashing?"
git diff | tp ask "Write a commit message for these changes"
tp ask "What is the command to undo a git commit?"
```

### Optional: Custom Rules
You can inject custom system prompts (personas) by feeding it a text or markdown file:
```bash
tp start --rule rules.md
```
