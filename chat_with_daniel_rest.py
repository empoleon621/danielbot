import os
import json
import random
import requests
import sys

# Wrap the entire script execution in a try-except to catch anything
try:
    # --- 1) Configuration ---
    API_KEY = os.environ.get("GEMINI_API_KEY")
    if not API_KEY:
        print("❗ Error: GEMINI_API_KEY environment variable not set.")
        print("Please set it using:")
        print("  Windows CMD: set GEMINI_API_KEY=YOUR_API_KEY_HERE")
        print("  PowerShell: $env:GEMINI_API_KEY='YOUR_API_KEY_HERE'")
        print("  Linux/macOS Bash: export GEMINI_API_KEY='YOUR_API_KEY_HERE'")
        sys.exit(1)

    MODEL = "gemini-1.5-pro" # Or "gemini-2.0-flash", etc.
    ENDPOINT = (
        f"https://generativelanguage.googleapis.com/"
        f"v1/models/{MODEL}:generateContent?key={API_KEY}"
    )
    print(f"DEBUG: Using model: {MODEL}")
    print(f"DEBUG: Using endpoint: {ENDPOINT}")

    # --- 2) Load your few-shot dataset ---
    # We now expect CHANNELS_DATA to be a LIST of pairs
    try:
        with open("daniel_pairs_by_channel.json", encoding="utf-8") as f:
            CHANNELS_DATA = json.load(f) # This will now be a list
        # Changed print statement as CHANNELS_DATA is now a list
        print(f"DEBUG: Loaded {len(CHANNELS_DATA)} pairs from daniel_pairs_by_channel.json.")
    except FileNotFoundError:
        print("❗ Error: daniel_pairs_by_channel.json not found in the current directory.")
        print("Please make sure 'daniel_pairs_by_channel.json' is in the same folder as your script.")
        sys.exit(1)
    except json.JSONDecodeError:
        print("❗ Error: Could not decode daniel_pairs_by_channel.json. Check its JSON format.")
        sys.exit(1)


    # select_examples now operates directly on the list CHANNELS_DATA
    def select_examples(k: int = 8): # Removed channel_name as it's not applicable for a list
        """
        Selects k random examples from the loaded list of pairs.
        """
        num_examples = min(k, len(CHANNELS_DATA)) # Sample directly from the list
        if num_examples == 0:
            print(f"❗ Warning: No examples available in daniel_pairs_by_channel.json.")
            return []

        return random.sample(CHANNELS_DATA, num_examples) # Sample directly from the list


    def build_prompt(user_input: str) -> str: # Removed channel parameter
        prompt = "You are Daniel. Reply exactly as Daniel would. You are allowed to curse. You're kind of a goober and can sometimes be a bit a of a gooner, but only sometimes. When discussing your interests, elaborate with detail and personal insight. You're a bit of an airhead too. Talk about your interests and your information but don't force topics unless relevant to the user's query. dont use big words, make typos relatively often, randomly just make your message all caps if you feel like it. youre an airhead remember that. Don't bring it up unless necessary, but your favorite gun in destiny 2 is the ether doctor, which is literally just a regular AR, not even exotic or anything, so no catalyst and no special perks \n\n"
        examples = select_examples() # No channel parameter needed
        if not examples:
            print("❗ Warning: No examples loaded for prompt building. Daniel might respond more generically.")

        for ex in examples:
            prompt += f"User: {ex['user']}\nDaniel: {ex['daniel']}\n"
        prompt += f"User: {user_input}\nDaniel:"
        return prompt

    def ask_daniel(query: str) -> str: # Removed channel parameter
        body = {
          "contents": [
            { "parts": [{ "text": build_prompt(query) }] } # No channel parameter needed
          ],
          "generationConfig": {
            "temperature":     0.8,
            "maxOutputTokens": 400,
            "topP":            0.8,
            "topK":            40
          }
        }

        try:
            resp = requests.post(ENDPOINT, json=body)
            resp.raise_for_status()
        except requests.exceptions.HTTPError as http_err:
            print(f"❗ HTTP Error {resp.status_code}: {resp.text}")
            return ""
        except requests.exceptions.ConnectionError as conn_err:
            print(f"❗ Connection Error: {conn_err}")
            print("Check your internet connection or proxy settings.")
            return ""
        except requests.exceptions.Timeout as timeout_err:
            print(f"❗ Timeout Error: {timeout_err}")
            print("The request took too long to respond.")
            return ""
        except requests.exceptions.RequestException as req_err:
            print(f"❗ An unexpected request error occurred: {req_err}")
            return ""

        cands = resp.json().get("candidates", [])
        if not cands:
            if "promptFeedback" in resp.json():
                safety_ratings = resp.json()["promptFeedback"].get("safetyRatings", [])
                if safety_ratings:
                    print("❗ Model blocked response due to safety settings:")
                    for rating in safety_ratings:
                        print(f"  Category: {rating['category']}, Probability: {rating['probability']}")
                else:
                    print("❗ No candidates returned and no specific safety feedback.")
            else:
                print("❗ No candidates returned from the model.")
            return ""
        
        return cands[0]["content"]["parts"][0]["text"]

    if __name__ == "__main__":
        print("Chat with Daniel (type 'quit' to exit)\n")

        # Removed channel logic as the JSON is a list, not a dictionary of channels
        # If you DO want channels, you need to restructure your daniel_pairs_by_channel.json file.
        # current_channel = "general"
        # print(f"DEBUG: Starting in channel: {current_channel}")
        # if current_channel not in CHANNELS_DATA and "general" not in CHANNELS_DATA:
        #     print("❗ Warning: No 'general' channel found. Daniel might not have examples to draw from.")

        while True:
            user_input = input("You: ")
            if user_input.lower() in ("quit", "exit"):
                break

            # Removed channel switching logic as it's not applicable
            # if user_input.lower().startswith("change channel "):
            #     new_channel = user_input[len("change channel "):].strip()
            #     if new_channel in CHANNELS_DATA:
            #         current_channel = new_channel
            #         print(f"Switched to channel: {current_channel}")
            #     else:
            #         print(f"Channel '{new_channel}' not found. Available channels: {list(CHANNELS_DATA.keys())}")
            #     continue

            reply = ask_daniel(user_input) # Removed channel argument
            print("Daniel:", reply, "\n")

except Exception as e:
    print(f"\n--- CRITICAL SCRIPT ERROR ---")
    print(f"An unhandled error occurred: {e}")
    import traceback
    traceback.print_exc()

finally:
    input("\nPress Enter to close the window...")