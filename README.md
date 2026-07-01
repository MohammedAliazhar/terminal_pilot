# Terminal Pilot

A minimalist, interactive CLI tool to connect to OpenRouter and chat with free AI models directly from your terminal.

## Installation

You can install Terminal Pilot globally directly from PyPI:
```bash
pip install Terminal-Pilot
```

## Configuration

Zero configuration required! 

Just run `tp start`. If you don't have an OpenRouter API key set up, the CLI will interactively ask you for it and securely save it for future sessions.

If you ever need to update or change your OpenRouter API key, just run:
```bash
tp auth
```

## Usage

Start the interactive assistant from anywhere in your terminal:

```bash
tp start
```

Inside the interactive chat, you can instantly load files into the AI's memory by using the `/read` command. You can read files in your current folder, or provide paths to files in other folders:
```text
? You: /read requirements.md
✓ Reading requirements.md...
? You: /read src/components/App.jsx
✓ Reading src/components/App.jsx...
? You: /read C:\Users\azhar\Desktop\error.log
✓ Reading C:\Users\azhar\Desktop\error.log...
? You: Give me a summary of these files.
```

### Project Context Awareness
You can instantly make the AI aware of your entire project structure. Just type `/context` in the chat, and Terminal Pilot will scan your current directory tree and inject key files (like `README.md`, `package.json`, `pyproject.toml`) into the AI's memory:
```text
? You: /context
✓ Scanning project directory for context...
```

### Auto Code Extraction
When the AI generates code, Terminal Pilot automatically detects markdown code blocks and offers to save them directly to your files:
```text
? Save generated code to files? (y/N) y

Block 1:
print("Hello World")
? Save this block? (Y/n) y
? File path (leave empty to skip): src/main.py
✓ Saved to src/main.py
```

### Changing Models Mid-Chat
If a model hits a rate limit or you want to switch to a different one, you don't need to exit. Just type `/model` to hot-swap:
```text
? You: /model
✓ Switched model to: google/gemma-3
```

### Clearing Chat Memory
If the chat history is getting too long or you want to remove any loaded rules, just type `/clear`. This instantly wipes the AI's memory of the conversation and re-applies your default persona.
```text
? You: /clear
✓ Chat memory and rules cleared! (Default rule re-applied)
```

### API Key Rotation
If you hit an OpenRouter rate limit (429 Error), Terminal Pilot can seamlessly fallback to a secondary API key. Simply provide multiple keys separated by commas in your `.env` or during `tp auth`.
```env
OPENROUTER_API_KEY="sk-or-v1-key1,sk-or-v1-key2"
```
The CLI will automatically cycle through the keys if one gets rate-limited, preventing chat interruptions.

### Token Dieting
To prevent your chat from crashing due to large context limits, Terminal Pilot tracks your token usage live (displayed above every AI response). If your chat history exceeds ~6,000 tokens, the "Token Diet" automatically activates—silently pruning older messages while preserving your system rules and newest messages to keep the AI fast and focused.

### Pipe Support (stdin)
You can pipe data directly into the AI to analyze logs, code, or command outputs instantly without opening an interactive chat:

```bash
cat error.log | tp ask "Why is this crashing?"
git diff | tp ask "Write a commit message for these changes"
tp ask "What is the command to undo a git commit?"
```

### Personas & Rules

Terminal Pilot ships with a **default persona** out of the box (a lazy senior developer focused on YAGNI). To disable or modify the default persona, simply edit or clear the `~/.terminal_pilot_default.md` file that gets automatically generated in your home directory.

You can hot-swap the AI's personality or rules at any point—even mid-chat—using the `/rule` command:

```text
? You: /rule concise
✓ Rule loaded mid-chat: concise
```

Terminal Pilot supports several ways to load rules:
1. **Built-in Personas**: Use our pre-configured shortcuts (e.g., `ponytail`, `pirate`, `concise`, `clear`, `tutor`, `yoda`).
2. **Local Files & Remote URLs**: Pass any `.md` file or raw URL (`/rule https://raw.github.../prompt.md`).
3. **Your Custom Aliases**: Create a `~/.terminal_pilot_rules.json` file in your home directory with your own shortcuts:
   ```json
   {
     "hacker": "You are a 90s movie hacker...",
     "expert": "You are a senior python developer..."
   }
   ```
   Then simply type `/rule hacker` anywhere!

You can also start the CLI with specific rules instantly (and chain them):
```bash
tp start --rule pirate
tp start --rule https://example.com/rule.md --rule concise
```
