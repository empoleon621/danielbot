import os
import requests
import json
import sys

API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    print("Error: GEMINI_API_KEY environment variable not set.")
    sys.exit(1)

list_models_url = f"https://generativelanguage.googleapis.com/v1/models?key={API_KEY}" # Note: v1 for ListModels

print(f"Attempting to list models from: {list_models_url}")

try:
    response = requests.get(list_models_url)
    response.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
    models_data = response.json()

    found_generative_models = False
    print("\n--- Available Models for your API Key ---")
    for model in models_data.get('models', []):
        name = model.get('name')
        displayName = model.get('displayName')
        supported_methods = model.get('supportedGenerationMethods')

        if supported_methods and "generateContent" in supported_methods:
            found_generative_models = True
            print(f"  Name: {name}")
            print(f"  Display Name: {displayName}")
            print(f"  Supports generateContent: Yes")
            print(f"  Supported Methods: {', '.join(supported_methods)}")
            print("-" * 40) # Separator for readability

    if not found_generative_models:
        print("No models found that explicitly support 'generateContent' for your API key.")
        print("This might indicate an issue with your API key's provisioning or regional availability.")
        print("Consider checking your Google Cloud project settings and API Key restrictions.")

except requests.exceptions.RequestException as e:
    print(f"Error fetching models: {e}")
    if hasattr(e, 'response') and e.response is not None:
        print(f"Response status code: {e.response.status_code}")
        print(f"Response content: {e.response.text}")

print("\n--- End of Model List ---")

# Add this line at the very end of the script:
input("\nPress Enter to close the window...")