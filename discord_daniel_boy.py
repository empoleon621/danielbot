import os
import json
import random
import requests
import sys
import discord # Import the discord.py library

# --- 1) Configuration for Gemini API ---
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    print("❗ Error: GEMINI_API_KEY environment variable not set.")
    print("Please set it using:")
    print("  Windows CMD: set GEMINI_API_KEY=YOUR_GEMINI_API_KEY_HERE")
    print("  PowerShell: $env:GEMINI_API_KEY='YOUR_GEMINI_API_KEY_HERE'")
    print("  Linux/macOS Bash: export GEMINI_API_KEY='YOUR_GEMINI_API_KEY_HERE'")
    sys.exit(1)

# The model to use for generating content (e.g., 'gemini-1.5-pro', 'gemini-2.0-flash', 'gemini-1.5-flash')
MODEL = "gemini-1.5-pro" # You can change this based on your preference and availability
ENDPOINT = (
    f"https://generativelanguage.googleapis.com/"
    f"v1/models/{MODEL}:generateContent?key={API_KEY}"
)
print(f"DEBUG: Using Gemini model: {MODEL}")
print(f"DEBUG: Using Gemini endpoint: {ENDPOINT}")

# --- 2) Load your few-shot dataset for Daniel's personality ---
try:
    with open("daniel_pairs_by_channel.json", encoding="utf-8") as f:
        CHANNELS_DATA = json.load(f)
    print(f"DEBUG: Loaded {len(CHANNELS_DATA)} pairs from daniel_pairs_by_channel.json.")
except FileNotFoundError:
    print("❗ Error: daniel_pairs_by_channel.json not found in the current directory.")
    print("Please make sure 'daniel_pairs_by_channel.json' is in the same folder as your script.")
    sys.exit(1)
except json.JSONDecodeError:
    print("❗ Error: Could not decode daniel_pairs_by_channel.json. Check its JSON format.")
    sys.exit(1)
except Exception as e:
    print(f"❗ An unexpected error occurred during data loading: {e}")
    sys.exit(1)

# --- Daniel's Core AI Functions (Copied from your previous script) ---
def select_examples(k: int = 8):
    """
    Selects k random examples from the loaded list of pairs.
    """
    num_examples = min(k, len(CHANNELS_DATA))
    if num_examples == 0:
        print(f"❗ Warning: No examples available in daniel_pairs_by_channel.json.")
        return []
    return random.sample(CHANNELS_DATA, num_examples)

def build_prompt(user_input: str) -> str:
    """
    Constructs a plain-text few-shot prompt for the model.
    Includes a system instruction for Daniel's persona and relevant examples.
    """
    # Refined system instruction for Daniel's persona
    prompt = "You are Daniel. Reply exactly as Daniel would. You are allowed to curse. When ASKED about your interests (like games, anime, music, IT studies at CSUN, working at Lorelles Coffee Shop, or going to the gym. Your favorite manga is berserk), elaborate with detail and personal insight, but do NOT just bring up going to the gym, lorelle's coffee shop, or csun for literally no reason. Engage in thoughtful conversation, but don't force topics unless relevant to the user's query. Avoid using overly enthusiastic phrases like chefs kiss and stuff like that. remember youre like a 20 year old kind of nerdy guy whos and airhead and heavy into meme/internet culture, but not corny like reddit dialogue. talk normalish. You also don't play any riot games games ie. league and valorant. \n\n"

    examples = select_examples()
    if not examples:
        print("❗ Warning: No examples loaded for prompt building. Daniel might respond more generically.")

    for ex in examples:
        prompt += f"User: {ex['user']}\nDaniel: {ex['daniel']}\n"
    
    prompt += f"User: {user_input}\nDaniel:"
    return prompt

def ask_daniel(query: str) -> str:
    """
    Sends the constructed prompt to the Gemini API and returns Daniel's response.
    """
    body = {
      "contents": [
        { "parts": [{ "text": build_prompt(query) }] }
      ],
      "generationConfig": {
        "temperature":     0.6,   # Adjust for creativity (0.0-1.0)
        "maxOutputTokens": 300,   # Max length of Daniel's response
        "topP":            0.5,
        "topK":            40
      }
    }

    try:
        resp = requests.post(ENDPOINT, json=body)
        resp.raise_for_status() # Raise an exception for HTTP errors (4xx or 5xx)
    except requests.exceptions.HTTPError as http_err:
        error_details = ""
        try:
            error_json = http_err.response.json()
            error_message = error_json.get("error", {}).get("message", "No specific error message.")
            error_details = f": {error_message}"
        except json.JSONDecodeError:
            error_details = f": {http_err.response.text}"
        print(f"❗ HTTP Error {resp.status_code}{error_details}")
        return "Daniel is momentarily offline due to an API error. Try again later."
    except requests.exceptions.ConnectionError as conn_err:
        print(f"❗ Connection Error: {conn_err}")
        print("Check your internet connection or proxy settings.")
        return "Daniel can't connect to the internet right now."
    except requests.exceptions.Timeout as timeout_err:
        print(f"❗ Timeout Error: {timeout_err}")
        print("The request took too long to respond.")
        return "Daniel took too long to respond. Try again."
    except requests.exceptions.RequestException as req_err:
        print(f"❗ An unexpected request error occurred: {req_err}")
        return "Daniel encountered an unexpected issue."

    cands = resp.json().get("candidates", [])
    if not cands:
        if "promptFeedback" in resp.json():
            safety_ratings = resp.json()["promptFeedback"].get("safetyRatings", [])
            if safety_ratings:
                blocked_categories = ", ".join([r['category'] for r in safety_ratings if r['probability'] in ['HIGH', 'MEDIUM']])
                print(f"❗ Model blocked response due to safety settings: {blocked_categories}")
                return "Daniel can't respond to that, it might violate safety guidelines."
            else:
                print("❗ No candidates returned and no specific safety feedback.")
        else:
            print("❗ No candidates returned from the model.")
        return "Daniel is drawing a blank. Try rephrasing?"
    
    return cands[0]["content"]["parts"][0]["text"]

# --- Discord Bot Setup ---
# Get your Discord bot token - MUST be set as an environment variable
DISCORD_BOT_TOKEN = os.environ.get("DISCORD_BOT_TOKEN")
if not DISCORD_BOT_TOKEN:
    print("❗ Error: DISCORD_BOT_TOKEN environment variable not set.")
    print("Please set it using:")
    print("  Windows CMD: set DISCORD_BOT_TOKEN=YOUR_DISCORD_BOT_TOKEN_HERE")
    print("  PowerShell: $env:DISCORD_BOT_TOKEN='YOUR_DISCORD_BOT_TOKEN_HERE'")
    print("  Linux/macOS Bash: export DISCORD_BOT_TOKEN='YOUR_DISCORD_BOT_TOKEN_HERE'")
    sys.exit(1)

# Set up Discord intents - crucial for receiving messages
# The 'message_content' intent is privileged and must be enabled in Discord Developer Portal
intents = discord.Intents.default()
intents.message_content = True
intents.members = True # Optional: if you need info about server members later

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    """Called when the bot successfully connects to Discord."""
    print(f'🤖 Logged in as {client.user} (ID: {client.user.id})')
    print('Bot is ready to receive commands!')
    # Set the bot's activity/status
    await client.change_presence(activity=discord.Game(name="Chatting with Daniel"))

@client.event
async def on_message(message):
    """Called when a message is sent in any channel the bot can see."""
    # Ignore messages sent by the bot itself to prevent infinite loops
    if message.author == client.user:
        return

    # Check if the bot was mentioned in the message
    # message.clean_content removes mentions from the text
    if client.user.mentioned_in(message):
        # Extract the part of the message after the bot's mention
        user_query = message.clean_content.replace(f'<@!{client.user.id}>', '').strip()

        if not user_query: # If the user just mentioned the bot without a question
            await message.channel.send(f"Yes, {message.author.mention}? What do you need?")
            return

        print(f"User '{message.author}' ({message.author.id}) mentioned Daniel with: '{user_query}'")

        # Show 'typing...' status while processing the request
        async with message.channel.typing():
            # Call your ask_daniel function with the user's query
            daniel_response = ask_daniel(user_query)
            
            # Send Daniel's response back to the channel
            await message.channel.send(f"{message.author.mention} {daniel_response}")
            print(f"Daniel responded: '{daniel_response}'")

    # Optional: You can also add a prefix command here if you prefer (e.g., !daniel what's up?)
    # prefix = "!daniel"
    # if message.content.lower().startswith(prefix):
    #     user_query = message.content[len(prefix):].strip()
    #     if not user_query:
    #         await message.channel.send(f"Yes, {message.author.mention}? What do you need?")
    #         return
    #     print(f"User '{message.author}' used prefix: '{user_query}'")
    #     async with message.channel.typing():
    #         daniel_response = ask_daniel(user_query)
    #         await message.channel.send(f"{message.author.mention} {daniel_response}")
    #     print(f"Daniel responded: '{daniel_response}'")


# --- Run the Bot ---
if __name__ == "__main__":
    try:
        client.run(DISCORD_BOT_TOKEN)
    except discord.LoginFailure:
        print("❗ Error: Invalid Discord Bot Token. Please check your DISCORD_BOT_TOKEN environment variable.")
    except Exception as e:
        print(f"\n--- CRITICAL SCRIPT ERROR ---")
        print(f"An unhandled error occurred while running the Discord bot: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # This will keep the console open for debugging if the bot crashes
        input("\nPress Enter to close the console...")