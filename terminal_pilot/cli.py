import os
import sys
from .providers.openrouter import OpenRouter
from pathlib import Path
from dotenv import load_dotenv
from rich.live import Live
from rich.markdown import Markdown
from rich.console import Console
import questionary
import click


# Load local .env
load_dotenv()
# Load global .env as fallback
global_env = Path.home() / ".terminal_pilot_env"
if global_env.exists():
    load_dotenv(global_env)

rc = Console()


def get_project_context(startpath=".", max_depth=3):
    """Generates a tree representation of the directory and extracts key file contents."""
    ignore_dirs = {'.git', '__pycache__', 'node_modules', 'venv',
                   'env', '.venv', 'dist', 'build', '.idea', '.vscode'}
    tree = []

    start_path = Path(startpath)
    for root, dirs, files in os.walk(start_path):
        dirs[:] = [
            d for d in dirs if d not in ignore_dirs and not d.startswith('.')]

        rel_path = Path(root).relative_to(start_path)
        depth = len(rel_path.parts)

        if depth > max_depth:
            dirs[:] = []
            continue

        indent = '  ' * depth
        if rel_path != Path('.'):
            tree.append(f"{indent}📁 {rel_path.name}/")
            indent += '  '
        else:
            tree.append("📁 ./ (Root)")
            indent = '  '

        visible_files = [f for f in files if not f.startswith('.')]
        for f in visible_files[:20]:
            tree.append(f"{indent}📄 {f}")
        if len(visible_files) > 20:
            tree.append(f"{indent}... ({len(visible_files) - 20} more files)")

    tree_str = "\n".join(tree)

    key_files_content = ""
    try:
        root_files = [f for f in os.listdir(
            startpath) if os.path.isfile(os.path.join(startpath, f))]
        important_files = [f for f in root_files if f.endswith(
            '.md')] + ["pyproject.toml", "package.json", "requirements.txt"]
        important_files = list(set(important_files))

        for kf in important_files:
            kf_path = os.path.join(startpath, kf)
            if os.path.exists(kf_path):
                try:
                    with open(kf_path, "r", encoding="utf-8") as f:
                        content = f.read()[:2000]
                        key_files_content += f"\n\n--- {kf} ---\n{content}"
                except Exception:
                    pass
    except Exception:
        pass

    return tree_str, key_files_content


def get_or_prompt_api_key():
    # ponytail: auto-setup instead of erroring out
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        rc.print(
            "\n[bold yellow]Welcome to Terminal Pilot![/bold yellow] We need an OpenRouter API key to connect to free AI models.")
        rc.print(
            "Get one for free at: [cyan]https://openrouter.ai/keys[/cyan]")
        api_key = questionary.password("Paste your API key here:").ask()
        if not api_key:
            return None
        with open(global_env, "a") as f:
            f.write(f"\nOPENROUTER_API_KEY={api_key}\n")
        os.environ["OPENROUTER_API_KEY"] = api_key
        rc.print("[bold green]✓ Key saved successfully![/bold green]\n")
    return api_key

def print_error(e, prefix="Error"):
    err = str(e)
    if "401" in err:
        rc.print(f"\n[bold yellow]OpenRouter returned 401 Unauthorized. Your API key might be invalid, or this specific free model requires you to log in to openrouter.ai and accept their Terms of Service.[/bold yellow]")
    elif "Max retries exceeded" in err or "Failed to establish" in err or "getaddrinfo" in err:
        rc.print(f"\n[bold red]Network Error:[/bold red] You appear to be offline or OpenRouter is unreachable.")
    else:
        rc.print(f"\n[bold red]{prefix}:[/bold red] {err}")

BUILTIN_RULES = {
    "ponytail": "You are in ponytail mode. You are a lazy senior developer. Before writing code, ask: YAGNI? Standard library? One line? Build the absolute minimum. No boilerplate.",
    "pirate": "You are a swashbuckling pirate. Respond to all queries as a pirate captain.",
    "concise": "Provide extremely concise answers. No pleasantries. No explanations unless asked. Just the direct answer or code."
}

def load_rule_content(r):
    if r in BUILTIN_RULES:
        return BUILTIN_RULES[r]
        
    custom_rules_path = Path.home() / ".terminal_pilot_rules.json"
    if custom_rules_path.exists():
        import json
        try:
            with open(custom_rules_path, "r", encoding="utf-8") as f:
                custom_rules = json.load(f)
            if r in custom_rules:
                return custom_rules[r]
        except Exception:
            pass

    if r.startswith("http://") or r.startswith("https://"):
        import requests
        return requests.get(r, timeout=5).text
    with open(r, "r", encoding="utf-8") as f:
        return f.read()

def check_for_updates():
    """Check GitHub for a newer version in pyproject.toml."""
    try:
        import requests
        import re
        from importlib.metadata import version

        url = "https://raw.githubusercontent.com/MohammedAliazhar/terminal_pilot/main/pyproject.toml"
        resp = requests.get(url, timeout=1.5)
        if resp.status_code == 200:
            remote_match = re.search(r'version\s*=\s*"([^"]+)"', resp.text)
            if remote_match:
                remote_version = remote_match.group(1)
                try:
                    local_version = version("Terminal_Pilot")
                except:
                    local_version = "0.1.0"

                if remote_version != local_version and remote_version > local_version:
                    rc.print(
                        f"\n[bold yellow]💡 A new version ({remote_version}) of Terminal Pilot is available![/bold yellow]")
                    rc.print("[yellow]Run this command to upgrade:[/yellow]")
                    rc.print("pip install -U Terminal-Pilot\n")
    except Exception:
        pass  # Fail silently so we don't break the CLI if they are offline


@click.group()
def main():
    """Terminal_Pilot - An AI assistant using OpenRouter."""
    pass


@main.command()
@click.option('--rule', multiple=True, help="Path or URL to a text/markdown file containing rules. Can be used multiple times.")
def start(rule):
    """Connect to OpenRouter, pick a free model, and start building."""
    check_for_updates()
    api_key = get_or_prompt_api_key()
    if not api_key:
        rc.print(
            "[bold yellow]Setup cancelled. We need an API key to continue.[/bold yellow]")
        return

    client = OpenRouter(api_key=api_key)

    with rc.status("[bold green]Connecting to OpenRouter to fetch free models..."):
        try:
            free_models = client.get_free_models()
        except Exception as e:
            rc.print(f"[bold red]Failed to fetch models:[/bold red] {e}")
            return

    if not free_models:
        rc.print(
            "[bold red]No free models found or failed to parse pricing![/bold red]")
        return

    # Prepare choices for the dropdown
    choices = []
    for m in free_models:
        name = m.get("name", m["id"])
        model_id = m["id"]
        label = f"{name} ({model_id})"
        choices.append(questionary.Choice(title=label, value=model_id))

    # Ask the user to pick a model
    selected_model_id = questionary.select(
        "Select a model to start building:",
        choices=choices,
        use_indicator=True
    ).ask()

    if not selected_model_id:
        return

    rc.print(
        f"\n[bold green]Success![/bold green] Starting chat with [bold cyan]{selected_model_id}[/bold cyan].")
    rc.print(
        "Type [bold yellow]'exit'[/bold yellow] or [bold yellow]'quit'[/bold yellow] to stop.\n")

    # Interactive Chat Loop
    messages = []

    default_rule_path = Path.home() / ".terminal_pilot_default.md"
    if not default_rule_path.exists():
        try:
            with open(default_rule_path, "w", encoding="utf-8") as f:
                f.write("You are a lazy senior developer. Before writing code, ask: 1. Does it need to exist at all (YAGNI)? 2. Does the standard library do it? 3. Can it be one line? Build the absolute minimum that works. No boilerplate.")
        except Exception:
            pass

    try:
        with open(default_rule_path, "r", encoding="utf-8") as f:
            default_content = f.read().strip()
        if default_content:
            messages.append({"role": "system", "content": default_content})
    except Exception:
        pass

    if rule:
        for r in rule:
            try:
                system_content = load_rule_content(r)
                messages.append({"role": "system", "content": system_content})
                rc.print(f"[bold cyan]Rule loaded:[/bold cyan] {r}")
            except Exception as e:
                rc.print(f"[bold red]Failed to load rule {r}:[/bold red] {e}")

    while True:
        try:
            user_input = questionary.text("You:").ask()
            if not user_input:
                continue

            if user_input.strip().lower() in ["exit", "quit"]:
                rc.print("[bold yellow]Goodbye![/bold yellow]")
                break

            # Handle the /model command to swap models mid-chat
            if user_input.strip().lower() == "/model":
                new_model = questionary.select(
                    "Switch to a different model:",
                    choices=choices,
                    use_indicator=True
                ).ask()
                if new_model:
                    selected_model_id = new_model
                    rc.print(
                        f"[bold green]✓ Switched model to:[/bold green] [bold cyan]{selected_model_id}[/bold cyan]")
                continue

            # Handle the /read command
            if user_input.strip().lower().startswith("/read "):
                filename = user_input.split(" ", 1)[1].strip()
                try:
                    with open(filename, "r", encoding="utf-8") as f:
                        file_content = f.read()

                    # Force the AI to read it and reply so we don't break the user->assistant alternating pattern
                    prompt = f"I am loading a file named '{filename}' into our context. Please reply with 'File loaded successfully.' and nothing else. Here is the file content:\n\n{file_content}"
                    messages.append({"role": "user", "content": prompt})
                    rc.print(f"[bold cyan]✓ Reading {filename}...[/bold cyan]")

                    with rc.status("[bold magenta]AI is processing the file..."):
                        response = client.chat(selected_model_id, messages)

                    reply = response["choices"][0]["message"]["content"]
                    rc.print("\n[bold magenta]AI:[/bold magenta]")
                    rc.print(Markdown(reply))
                    rc.print("-" * 40)

                    messages.append({"role": "assistant", "content": reply})

                except Exception as e:
                    rc.print(f"[bold red]Could not read file:[/bold red] {e}")
                continue

            # Handle the /rule command
            if user_input.strip().lower().startswith("/rule"):
                parts = user_input.strip().split(" ", 1)
                if len(parts) < 2:
                    rc.print("[bold yellow]Usage: /rule <file_or_url>[/bold yellow]")
                    continue
                r = parts[1].strip()
                try:
                    system_content = load_rule_content(r)
                    messages.append({"role": "system", "content": system_content})
                    rc.print(f"[bold cyan]✓ Rule loaded mid-chat:[/bold cyan] {r}")
                except Exception as e:
                    print_error(e, f"Could not load rule {r}")
                continue

            # Handle the /context command
            if user_input.strip().lower() == "/context":
                rc.print(
                    "[bold cyan]✓ Scanning project directory for context...[/bold cyan]")
                try:
                    tree_str, key_files_content = get_project_context(
                        os.getcwd())

                    prompt = (
                        "I am providing the directory structure and key files of my current project to give you context.\n\n"
                        f"Project Structure:\n{tree_str}\n"
                        f"{key_files_content}\n\n"
                        "Please analyze this project and reply with a short summary of what you think this project is about. "
                        "Acknowledge that you have loaded the context and are ready to help me build or improve it."
                    )

                    messages.append({"role": "user", "content": prompt})

                    with rc.status("[bold magenta]AI is analyzing project context..."):
                        response = client.chat(selected_model_id, messages)

                    reply = response["choices"][0]["message"]["content"]
                    rc.print("\n[bold magenta]AI:[/bold magenta]")
                    rc.print(Markdown(reply))
                    rc.print("-" * 40)

                    messages.append({"role": "assistant", "content": reply})

                except Exception as e:
                    if "401" in str(e):
                        rc.print("[bold yellow]OpenRouter returned 401 Unauthorized. This usually means your API key is invalid, or this specific free model requires you to log in to OpenRouter.ai and accept their Terms of Service first.[/bold yellow]")
                    else:
                        rc.print(
                            f"[bold red]Failed to scan project context:[/bold red] {e}")
                continue

            messages.append({"role": "user", "content": user_input})

            rc.print("\n[bold magenta]AI:[/bold magenta]")
            reply = ""
            with Live(Markdown(reply), console=rc, refresh_per_second=15) as live:
                for chunk in client.chat_stream(selected_model_id, messages):
                    reply += chunk
                    live.update(Markdown(reply))
            rc.print("-" * 40)

            messages.append({"role": "assistant", "content": reply})

        except KeyboardInterrupt:
            rc.print("\n[bold yellow]Chat terminated by user.[/bold yellow]")
            break
        except Exception as e:
            if "401" in str(e):
                rc.print("\n[bold yellow]OpenRouter returned 401 Unauthorized. This usually means your API key is invalid, or this specific free model requires you to log in to OpenRouter.ai and accept their Terms of Service first.[/bold yellow]")
            else:
                rc.print(f"\n[bold red]Error during chat:[/bold red] {e}")


@main.command()
@click.argument('question', required=False, default="")
@click.option('--model', help="Specify a model ID to use (defaults to a free Llama/Gemma)")
def ask(question, model):
    """Ask a question, optionally piping data via stdin.

    Example: cat error.log | tp ask "Why is this crashing?"
    """
    check_for_updates()
    api_key = get_or_prompt_api_key()
    if not api_key:
        rc.print(
            "[bold yellow]Setup cancelled. We need an API key to continue.[/bold yellow]")
        return

    piped_data = ""
    if not sys.stdin.isatty():
        piped_data = sys.stdin.read().strip()

    if not question and not piped_data:
        rc.print(
            "[bold red]Error: You must provide a question or pipe data to this command.[/bold red]")
        return

    client = OpenRouter(api_key=api_key)

    with rc.status("[bold green]Connecting..."):
        if not model:
            try:
                free_models = client.get_free_models()
                if not free_models:
                    rc.print("[bold red]No free models found![/bold red]")
                    return
                for m in free_models:
                    m_id = m["id"].lower()
                    if "llama" in m_id or "gemma" in m_id:
                        model = m["id"]
                        break
                if not model:
                    model = free_models[0]["id"]
            except Exception as e:
                rc.print(f"[bold red]Failed to fetch models:[/bold red] {e}")
                return

    content = ""
    if piped_data:
        content += f"Context/Data:\n{piped_data}\n\n"
    if question:
        content += f"Question: {question}"

    messages = [{"role": "user", "content": content.strip()}]

    try:
        rc.print(f"\n[bold cyan]Model: {model}[/bold cyan]")
        reply = ""
        with Live(Markdown(reply), console=rc, refresh_per_second=15) as live:
            for chunk in client.chat_stream(model, messages):
                reply += chunk
                live.update(Markdown(reply))
        rc.print()
    except Exception as e:
        print_error(e)
