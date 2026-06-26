import os
import click
import questionary
from rich.console import Console
from rich.markdown import Markdown
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

@click.group()
def main():
    """Terminal_Pilot - An AI assistant using OpenRouter."""
    pass

@main.command()
@click.option('--rule', type=click.Path(exists=True), help="Path to a text/markdown file containing rules (e.g., ponytail.md)")
def start(rule):
    """Connect to OpenRouter, pick a free model, and start building."""
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

    # Ask for use case
    rc.print("\n[bold cyan]Tell us about your use case to get a tailored model recommendation.[/bold cyan]")
    use_case = questionary.text(
        "What is your primary use case? (e.g., coding, writing a thesis) [Press Enter to skip]:"
    ).ask()

    recommended_model = None
    if use_case:
        use_case = use_case.lower()
        if any(kw in use_case for kw in ["code", "coding", "program", "developer", "software"]):
            # Find a coder model, prioritize deepseek or qwen coder
            for m in free_models:
                m_id = m["id"].lower()
                if "coder" in m_id or "deepseek" in m_id or "qwen" in m_id:
                    recommended_model = m
                    break
        elif any(kw in use_case for kw in ["thesis", "write", "writing", "essay", "content", "story"]):
            # Find a good general model for writing
            for m in free_models:
                m_id = m["id"].lower()
                if "llama" in m_id or "gemma" in m_id or "mistral" in m_id:
                    recommended_model = m
                    break

    # Prepare choices for the dropdown
    choices = []
    
    # If we have a recommendation, add it at the top
    if recommended_model:
        name = recommended_model.get("name", recommended_model["id"])
        model_id = recommended_model["id"]
        label = f"⭐ RECOMMENDED: {name} ({model_id})"
        choices.append(questionary.Choice(title=label, value=model_id))
        
    for m in free_models:
        # skip if we already added it as recommended
        if recommended_model and m["id"] == recommended_model["id"]:
            continue
            
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

            messages.append({"role": "user", "content": user_input})

            with rc.status("[bold magenta]AI is thinking..."):
                response = client.chat(selected_model_id, messages)

            reply = response["choices"][0]["message"]["content"]
            rc.print("\n[bold magenta]AI:[/bold magenta]")
            rc.print(Markdown(reply))
            rc.print("-" * 40)
            
            messages.append({"role": "assistant", "content": reply})

        except KeyboardInterrupt:
            rc.print("\n[bold yellow]Chat terminated by user.[/bold yellow]")
            break
        except Exception as e:
            rc.print(f"\n[bold red]Error during chat:[/bold red] {e}")
