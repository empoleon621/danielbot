import glob
import json

def main():
    print("🔍 Scanning for JSON files…")
    files = glob.glob("*.json")
    print(f"Found {len(files)} JSON files.")

    all_msgs = []
    for i, path in enumerate(files, 1):
        print(f"[{i}/{len(files)}] Loading {path}…", end="\r")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        # Accept both list and dict-based JSON exports
        if isinstance(data, list):
            msgs = data
        else:
            msgs = data.get("messages", data.get("Messages", [])) or []
        all_msgs.extend(msgs)
    print(f"\n✅ Loaded a total of {len(all_msgs)} messages.")

    print("🔃 Sorting messages by timestamp…")
    # ISO-8601 timestamps sort lexicographically; handle both keys
    all_msgs.sort(key=lambda m: m.get("timestamp", m.get("Timestamp", "")))

    # Replace with actual IDs
    DANIEL_ID = "391754309840404492"
    # If you want only your messages, set MY_ID below; otherwise leave None
    MY_ID = None  # e.g. "123456789012345678"

    pairs = []
    for i, msg in enumerate(all_msgs):
        author = msg.get("author", {}) or msg.get("Author", {})
        author_id = author.get("id") or author.get("Id")
        if author_id == DANIEL_ID:
            channel_id = msg.get("channel_id") or msg.get("ChannelId")
            # Walk back to find the last non-Daniel (or optionally your) message in the same channel
            j = i - 1
            while j >= 0:
                prev = all_msgs[j]
                prev_auth = prev.get("author", {}) or prev.get("Author", {})
                prev_id = prev_auth.get("id") or prev_auth.get("Id")
                prev_chan = prev.get("channel_id") or prev.get("ChannelId")
                if prev_chan == channel_id and prev_id != DANIEL_ID and (MY_ID is None or prev_id == MY_ID):
                    user_msg = prev.get("content") or prev.get("Content", "")
                    daniel_msg = msg.get("content") or msg.get("Content", "")
                    user_text = user_msg.strip()
                    daniel_text = daniel_msg.strip()
                    if user_text and daniel_text:
                        pairs.append({"user": user_text, "daniel": daniel_text})
                    break
                j -= 1

    output = "daniel_pairs_by_channel.json"
    with open(output, "w", encoding="utf-8") as out:
        json.dump(pairs, out, indent=2, ensure_ascii=False)

    print(f"🗂 Generated {len(pairs)} pairs in {output}")

if __name__ == "__main__":
    main()
