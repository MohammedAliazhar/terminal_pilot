import os
import click
import questionary
from rich.console import Console
from rich.markdown import Markdown
from rich.live import Live
from dotenv import load_dotenv
from pathlib import Path

from .providers.openrouter import OpenRouter

# Load local .env
load_dotenv()
# Load global .env as fallback
global_env = Path.home() / ".terminal_pilot_env"
if global_env.exists():
    load_dotenv(global_env)

rc = Console()

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
                    rc.print(f"\n[bold yellow]💡 A new version ({remote_version}) of Terminal Pilot is available![/bold yellow]")
                    rc.print("[yellow]Run this command to upgrade:[/yellow]")
                    rc.print("pip install -U Terminal-Pilot\n")
    except Exception:
        pass # Fail silently so we don't break the CLI if they are offline

@click.group()
def main():
    """Terminal_Pilot - An AI assistant using OpenRouter."""
    pass

@main.command()
@click.option('--rule', type=click.Path(exists=True), help="Path to a text/markdown file containing rules (e.g., ponytail.md)")
def start(rule):
    """Connect to OpenRouter, pick a free model, and start building."""
    check_for_updates()
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        rc.print("[bold red]Error: OPENROUTER_API_KEY not found in .env file.[/bold red]")
        rc.print("Please add it to your .env file in the format OPENROUTER_API_KEY=your_key")
        return

    client = OpenRouter(api_key=api_key)

    with rc.status("[bold green]Connecting to OpenRouter to fetch free models..."):
        try:
            free_models = client.get_free_models()
        except Exception as e:
            rc.print(f"[bold red]Failed to fetch models:[/bold red] {e}")
            return

    if not free_models:
        rc.print("[bold red]No free models found or failed to parse pricing![/bold red]")
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

    rc.print(f"\n[bold green]Success![/bold green] Starting chat with [bold cyan]{selected_model_id}[/bold cyan].")
    rc.print("Type [bold yellow]'exit'[/bold yellow] or [bold yellow]'quit'[/bold yellow] to stop.\n")

    # Interactive Chat Loop
    messages = []
    
    if rule:
        try:
            with open(rule, "r", encoding="utf-8") as f:
                system_content = f.read()
            messages.append({"role": "system", "content": system_content})
            rc.print(f"[bold cyan]Rule file loaded:[/bold cyan] {rule}")
        except Exception as e:
            rc.print(f"[bold red]Failed to load rule file:[/bold red] {e}")

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
                    rc.print(f"[bold green]✓ Switched model to:[/bold green] [bold cyan]{selected_model_id}[/bold cyan]")
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
            rc.print(f"\n[bold red]Error during chat:[/bold red] {e}")

import sys

@main.command()
@click.argument('question', required=False, default="")
@click.option('--model', help="Specify a model ID to use (defaults to a free Llama/Gemma)")
def ask(question, model):
    """Ask a question, optionally piping data via stdin.
    
    Example: cat error.log | tp ask "Why is this crashing?"
    """
    check_for_updates()
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        rc.print("[bold red]Error: OPENROUTER_API_KEY not found.[/bold red]")
        return
        
    piped_data = ""
    if not sys.stdin.isatty():
        piped_data = sys.stdin.read().strip()
        
    if not question and not piped_data:
        rc.print("[bold red]Error: You must provide a question or pipe data to this command.[/bold red]")
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
            rc.print(f"[bold red]Error:[/bold red] {e}")
