import os
import requests
from dotenv import load_dotenv
from pathlib import Path

# Load local .env
load_dotenv()
# Load global .env as fallback
global_env = Path.home() / ".terminal_pilot_env"
if global_env.exists():
    load_dotenv(global_env)

class OpenRouter:
    BASE_URL = "https://openrouter.ai/api/v1"

    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "http://localhost",
            "X-Title": "Terminal_Pilot"
        }

    def get_free_models(self):
        """Fetch models from OpenRouter and filter for free ones."""
        response = requests.get(f"{self.BASE_URL}/models", headers=self.headers)
        response.raise_for_status()
        data = response.json().get("data", [])
        
        free_models = []
        for model in data:
            pricing = model.get("pricing", {})
            prompt = pricing.get("prompt", "-1")
            completion = pricing.get("completion", "-1")
            
            try:
                prompt_price = float(prompt)
                completion_price = float(completion)
            except (ValueError, TypeError):
                continue
                
            # If the model explicitly has 0 pricing or ends with :free
            if (prompt_price == 0.0 and completion_price == 0.0) or model["id"].endswith(":free"):
                free_models.append(model)
                
        return free_models

    def chat(self, model_id, messages):
        """Send a chat completion request to OpenRouter."""
        payload = {
            "model": model_id,
            "messages": messages
        }
        response = requests.post(
            f"{self.BASE_URL}/chat/completions",
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()
