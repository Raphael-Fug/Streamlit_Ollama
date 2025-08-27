import requests

def get_ollama_models():
    try:
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code == 200:
            return response.json().get("models", [])
        else:
            return []
    except:
        return []