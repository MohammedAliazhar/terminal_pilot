# Terminal Pilot

A minimalist, interactive CLI tool to connect to OpenRouter and chat with free AI models directly from your terminal.

## Installation

1. Clone this repository:
   ```bash
   git clone <YOUR_GITHUB_REPO_URL>
   cd Terminal_Pilot
   ```

2. Install the CLI tool globally (or in a virtual environment):
   ```bash
   pip install -e .
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
# or
terminal_pilot start
```

### Optional: Custom Rules (e.g. Ponytail)
You can inject custom system prompts (personas) by feeding it a text or markdown file:
```bash
tp start --rule ponytail.md
```
