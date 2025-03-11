import re, html, os
from flask import Flask, request, jsonify
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from googletrans import Translator

app = Flask(__name__)
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
if not SLACK_BOT_TOKEN:
    raise ValueError("No SLACK_BOT_TOKEN!")
client = WebClient(token=SLACK_BOT_TOKEN)
translator = Translator()
BOT_ID = "U0899FAG7AA"

slack_custom_emoji_pattern = re.compile(r"<:([a-zA-Z0-9_\-+]+):[A-Za-z0-9]+>", re.IGNORECASE)
slack_shortcode_pattern = re.compile(r":([^:]+):", re.IGNORECASE)
unicode_emoji_pattern = re.compile("[" "\U0001F600-\U0001F64F" "\U0001F300-\U0001F5FF" "\U0001F680-\U0001F6FF" "\U0001F1E0-\U0001F1FF" "]+", flags=re.UNICODE)
url_pattern = re.compile(r"(https?://\S+|www\.\S+)", re.IGNORECASE)

def generate_placeholder(token_type, index):
    return f"<<<{token_type.lower()}_{index}>>>"

def replace_urls(text):
    replaced = text
    mapping = {}
    matches = url_pattern.findall(text)
    for i, url in enumerate(matches):
        ph = f"<<<URL_{i}>>>"
        mapping[ph] = url
        replaced = replaced.replace(url, ph, 1)
    return replaced, mapping

def restore_placeholder(text, placeholder, original):
    inside = placeholder[3:-3]
    pattern = re.compile(r"<<<\s*" + re.escape(inside) + r"\s*>>>", re.IGNORECASE)
    return pattern.sub(original, text)

def restore_urls(text, mapping):
    for ph, url in mapping.items():
        text = restore_placeholder(text, ph, url)
    return text

def replace_slack_custom_emojis(text):
    replaced = text
    mapping = {}
    matches = slack_custom_emoji_pattern.findall(text)
    for i, _ in enumerate(matches):
        m = slack_custom_emoji_pattern.search(replaced)
        if not m:
            continue
        full = m.group(0)
        ph = generate_placeholder("CSTM", i)
        mapping[ph] = full
        replaced = replaced.replace(full, ph, 1)
    return replaced, mapping

def restore_slack_custom_emojis(text, mapping):
    for ph, orig in mapping.items():
        text = restore_placeholder(text, ph, orig)
    return text

def replace_slack_shortcodes(text):
    replaced = text
    mapping = {}
    matches = slack_shortcode_pattern.findall(text)
    for i, sc_inner in enumerate(matches):
        full_sc = f":{sc_inner}:"
        ph = generate_placeholder("SC", i)
        mapping[ph] = full_sc
        replaced = replaced.replace(full_sc, ph, 1)
    return replaced, mapping

def restore_slack_shortcodes(text, mapping):
    for ph, sc in mapping.items():
        text = restore_placeholder(text, ph, sc)
    return text

def replace_unicode_emojis(text):
    replaced = text
    mapping = {}
    emojis = unicode_emoji_pattern.findall(text)
    for i, em in enumerate(emojis):
        ph = generate_placeholder("UE", i)
        mapping[ph] = em
        replaced = replaced.replace(em, ph, 1)
    return replaced, mapping

def restore_unicode_emojis(text, mapping):
    for ph, em in mapping.items():
        text = restore_placeholder(text, ph, em)
    return text

def replace_all_emojis(text):
    t1, mc = replace_slack_custom_emojis(text)
    t2, ms = replace_slack_shortcodes(t1)
    t3, mu = replace_unicode_emojis(t2)
    return t3, {"custom": mc, "shortcodes": ms, "unicode": mu}

def restore_all_emojis(text, maps):
    text = restore_unicode_emojis(text, maps["unicode"])
    text = restore_slack_shortcodes(text, maps["shortcodes"])
    text = restore_slack_custom_emojis(text, maps["custom"])
    return text

def fix_spacing(text):
    return re.sub(r'\.([A-Za-zА-Яа-я])', r'. \1', text)

def fix_link_translations(text):
    text = re.sub(r'(https?)\s*:\s*//', r'\1://', text)
    text = re.sub(r'www\.\s+', 'www.', text)
    text = re.sub(r'\. ([a-z]{2,})\b', r'.\1', text, flags=re.IGNORECASE)
    return text

# Премахва споменаването на бота от текста
def remove_bot_mentions(text):
    pattern = re.compile(r"<@([A-Za-z0-9]+)>")
    def repl(match):
        if match.group(1).upper() == BOT_ID.upper():
            return ""
        return match.group(0)
    return pattern.sub(repl, text)

@app.route("/slack/events", methods=["POST"])
def slack_events():
    data = request.json
    if "challenge" in data:
        print("Challenge received:", data["challenge"], flush=True)
        return jsonify({"challenge": data["challenge"]})
    if "event" in data:
        event = data["event"]
        print("Event:", event, flush=True)
        # Игнориране на съобщения от бота
        if event.get("user") == BOT_ID:
            print("Ignored bot message", flush=True)
            return jsonify({"status": "ignored"})
        # Игнориране на събития с subtype (напр. редактирани съобщения)
        if event.get("subtype"):
            print("Ignored message with subtype:", event.get("subtype"), flush=True)
            return jsonify({"status": "ignored"})
        if event.get("type") in ["message", "app_mention"]:
            channel_id = event.get("channel")
            user_id = event.get("user")
            text = event.get("text", "")
            if not text.strip():
                print("Ignored empty text message", flush=True)
                return jsonify({"status": "ignored"})
            # Ако съобщението не е в директно съобщение (DM),
            # проверяваме дали ботът е тагнат
            if not channel_id.startswith("D") and not re.search(rf"(?:<@{BOT_ID}>|Translator)", text, re.IGNORECASE):
                print("Bot is not mentioned in the message, ignoring.", flush=True)
                return jsonify({"status": "ignored"})
            thread_ts = event.get("thread_ts", event.get("ts"))
            print("Processing message:", text, flush=True)
            process_message(channel_id, user_id, text, thread_ts)
    return jsonify({"status": "ok"})

def get_user_name(user_id):
    try:
        r = client.users_info(user=user_id)
        n = r["user"].get("real_name") or r["user"].get("name")
        return n if n else f"User {user_id}"
    except Exception as e:
        print("Error getting user name:", e, flush=True)
        return f"User {user_id}"

def publish_message(channel_id, user_name, translated, thread_ts):
    msg = f"📝 Übersetzung von {user_name}: {translated}"
    try:
        client.chat_postMessage(channel=channel_id, text=msg, thread_ts=thread_ts)
        print("Published as reply:", msg, flush=True)
    except Exception as e:
        print("Error publishing message:", e, flush=True)

def process_message(channel_id, user_id, text, thread_ts):
    print("Starting processing for message:", text, flush=True)
    try:
        lang = translator.detect(text).lang
    except Exception as e:
        print("Error detecting language:", e, flush=True)
        return
    print("Detected language:", lang, flush=True)
    if lang not in ["en", "de"]:
        print("Language not supported; ignoring.", flush=True)
        return
    replaced_urls, map_urls = replace_urls(text)
    replaced_emojis, map_emojis = replace_all_emojis(replaced_urls)
    if lang == "en":
        tr = translator.translate(replaced_emojis, src="en", dest="de").text
    else:
        tr = translator.translate(replaced_emojis, src="de", dest="en").text
    tr = html.unescape(tr)
    tr = restore_all_emojis(tr, map_emojis)
    tr = restore_urls(tr, map_urls)
    tr = fix_spacing(tr)
    tr = fix_link_translations(tr)
    tr = remove_bot_mentions(tr)
    print("Final translated text:", tr, flush=True)
    user_name = get_user_name(user_id)
    publish_message(channel_id, user_name, tr, thread_ts)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=29874, debug=True)
