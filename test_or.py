import os
from dotenv import load_dotenv
from pathlib import Path
from terminal_pilot.providers.openrouter import OpenRouter

def test():
    global_env = Path.home() / ".terminal_pilot_env"
    if global_env.exists():
        load_dotenv(global_env, override=True)

    api_key = os.getenv("OPENROUTER_API_KEY")
    client = OpenRouter(api_key=api_key)
    try:
        response = client.chat("nvidia/nemotron-3-super-120b-a12b:free", [{"role": "user", "content": "Hello"}])
        print("Chat successful:", response)
    except Exception as e:
        print("Chat failed:", e)

if __name__ == "__main__":
    test()
