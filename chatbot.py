"""Rule-Based Interactive Terminal Assistant / Chatbot

Features:
  - Keyword + regex intent recognition (multi-intent: one message can match several intents)
  - Business hours, product FAQs, pricing, shipping, returns, contact, payments
  - Optional JSON FAQ dataset (faq.json) for extra questions
  - Conversational state: GREETING -> ACTIVE -> EXIT
  - Fallback handling for unrecognised queries
  - Clean exit commands: bye, exit, quit
  - Error handling (empty input, Ctrl+C, bad JSON)

Run with:  python chatbot.py
"""

import json
import os
import re
from datetime import datetime

BOT_NAME = "Dexter"
COMPANY = "TechNova"

# Business hours: Monday=0 ... Sunday=6 -> (open_hour, close_hour) in 24h
BUSINESS_HOURS = {0: (9, 18), 1: (9, 18), 2: (9, 18), 3: (9, 18), 4: (9, 18), 5: (10, 14)}

EXIT_WORDS = {"bye", "exit", "quit", "goodbye"}

# Intent -> regex patterns + response. Patterns are matched on normalized input.
INTENTS = {
    "greeting": {
        "patterns": [r"\b(hi|hello|hey|hola|good (morning|afternoon|evening))\b"],
        "response": f"Hello! Welcome to {COMPANY} support.",
    },
    "hours": {
        "patterns": [r"\b(hours?|timings?|open|close|opening|closing|working time|business time)\b"],
        "response": "HOURS",  # replaced by dynamic answer
    },
    "pricing": {
        "patterns": [r"\b(price|prices|pricing|cost|how much|plans?|subscription|fees?)\b"],
        "response": (f"{COMPANY} plans: Basic Rs.499/month, Pro Rs.999/month, "
                     "Enterprise Rs.2499/month. Annual billing gives 20% off."),
    },
    "shipping": {
        "patterns": [r"\b(shipping|delivery|deliver|ship|dispatch|track(ing)?|order status)\b"],
        "response": ("Standard delivery takes 3-5 business days, express takes 1-2 days. "
                     "Shipping is free above Rs.999. You get a tracking link by email after dispatch."),
    },
    "returns": {
        "patterns": [r"\b(return|refund|exchange|money back|cancel(lation)?)\b"],
        "response": ("You can return any product within 14 days of delivery for a full refund. "
                     "Refunds reach your account in 5-7 business days."),
    },
    "warranty": {
        "patterns": [r"\b(warranty|guarantee|repair|defect(ive)?|damaged|broken)\b"],
        "response": "All products carry a 1-year manufacturer warranty covering defects. Keep your invoice handy.",
    },
    "payment": {
        "patterns": [r"\b(pay|payment|upi|card|credit|debit|emi|net ?banking|cod|cash on delivery)\b"],
        "response": "We accept UPI, credit/debit cards, net banking, and cash on delivery. EMI is available on orders above Rs.5000.",
    },
    "contact": {
        "patterns": [r"\b(contact|phone|call|email|mail|human|agent|support|talk to|reach)\b"],
        "response": f"You can reach us at support@{COMPANY.lower()}.com or call 1800-123-4567 during business hours.",
    },
    "product": {
        "patterns": [r"\b(products?|catalog(ue)?|features?|what do you (sell|offer)|laptops?|phones?|accessories)\b"],
        "response": (f"{COMPANY} offers laptops, smartphones and accessories. "
                     "Ask about pricing, warranty or delivery for any of them."),
    },
    "thanks": {
        "patterns": [r"\b(thanks?|thank you|thx|great|awesome|helpful)\b"],
        "response": "You're welcome! Happy to help.",
    },
    "help": {
        "patterns": [r"\b(help|what can you do|options|menu)\b"],
        "response": ("I can help with: business hours, pricing, shipping, returns, warranty, "
                     "payments, and contact details. Type 'bye' to exit."),
    },
}


def normalize(text):
    """Lowercase, strip whitespace, remove extra punctuation and collapse spaces."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def load_faq_dataset(filename="faq.json"):
    """Load optional FAQ JSON (list of {'question':..., 'answer':...}). Returns [] on any problem."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):  # allow {"faqs": [...]} or {"question": "answer"}
            if "faqs" in data and isinstance(data["faqs"], list):
                data = data["faqs"]
            else:
                data = [{"question": q, "answer": a} for q, a in data.items()]
        faqs = [item for item in data
                if isinstance(item, dict) and "question" in item and "answer" in item]
        print(f"[Loaded {len(faqs)} extra FAQs from {filename}]")
        return faqs
    except (json.JSONDecodeError, OSError) as exc:
        print(f"[Could not read {filename}: {exc}. Using built-in answers only.]")
        return []


def hours_answer():
    """Dynamic answer: shows hours and whether we are open right now."""
    now = datetime.now()
    today = BUSINESS_HOURS.get(now.weekday())
    lines = ["Business hours: Mon-Fri 9:00 AM - 6:00 PM, Saturday 10:00 AM - 2:00 PM, Sunday closed."]
    if today and today[0] <= now.hour < today[1]:
        lines.append("We are OPEN right now.")
    else:
        lines.append("We are currently CLOSED, but you can email us anytime.")
    return " ".join(lines)


def match_intents(clean_text):
    """Return list of (intent_name, score) sorted best first. Multi-intent aware."""
    matches = []
    for name, data in INTENTS.items():
        score = sum(1 for p in data["patterns"] if re.search(p, clean_text))
        if score:
            matches.append((name, score))
    return sorted(matches, key=lambda m: -m[1])


def match_faq(clean_text, faqs, threshold=0.5):
    """Word-overlap confidence match against the JSON FAQ dataset."""
    user_words = set(clean_text.split())
    best, best_score = None, 0.0
    for item in faqs:
        q_words = set(normalize(item["question"]).split())
        if not q_words:
            continue
        score = len(user_words & q_words) / len(q_words)
        if score > best_score:
            best, best_score = item, score
    return best if best_score >= threshold else None


def extract_name(raw_text):
    """Pick up a name from 'my name is X' / 'I am X' / 'call me X'."""
    m = re.search(r"\b(?:my name is|i am|i'm|call me)\s+([A-Za-z]+)", raw_text, re.IGNORECASE)
    return m.group(1).capitalize() if m else None


def get_reply(raw_text, state, faqs):
    """Return (reply_text, new_state). state is a dict holding conversation context."""
    clean = normalize(raw_text)

    # 1. Exit commands (whole message or a word in it)
    if clean in EXIT_WORDS or any(w in EXIT_WORDS for w in clean.split()):
        state["stage"] = "EXIT"
        name = f", {state['name']}" if state.get("name") else ""
        return f"Goodbye{name}! Thanks for chatting with {COMPANY}. Have a great day!", state

    # 2. Remember the user's name (context)
    name = extract_name(raw_text)
    if name:
        state["name"] = name
        return f"Nice to meet you, {name}! How can I help you today?", state

    # 3. Intent matching (multi-intent)
    matches = match_intents(clean)
    if matches:
        state["fallbacks"] = 0
        state["stage"] = "ACTIVE"
        parts = []
        for intent, _ in matches[:3]:                    # answer up to 3 intents at once
            if intent == "greeting" and len(matches) > 1:
                continue                                 # skip hello if there is a real question too
            reply = hours_answer() if INTENTS[intent]["response"] == "HOURS" else INTENTS[intent]["response"]
            parts.append(reply)
        if matches[0][0] == "greeting" and state.get("name"):
            parts[0] = f"Hello again, {state['name']}!"
        return "\n".join(parts), state

    # 4. JSON FAQ dataset
    faq = match_faq(clean, faqs)
    if faq:
        state["fallbacks"] = 0
        state["stage"] = "ACTIVE"
        return faq["answer"], state

    # 5. Graceful fallback
    state["fallbacks"] = state.get("fallbacks", 0) + 1
    if state["fallbacks"] >= 2:
        return (f"I'm still not sure I understand. Please email support@{COMPANY.lower()}.com "
                "or type 'help' to see what I can answer."), state
    return "Sorry, I didn't quite get that. Could you rephrase? (Type 'help' to see what I can do.)", state


def main():
    faqs = load_faq_dataset()
    state = {"stage": "GREETING", "name": None, "fallbacks": 0}

    print("=" * 50)
    print(f"  {BOT_NAME} - {COMPANY} Virtual Assistant")
    print("  Type 'help' for options, or 'bye' / 'exit' / 'quit' to leave.")
    print("=" * 50)
    print(f"{BOT_NAME}: Hi! I'm {BOT_NAME}. What's your name, or how can I help?")

    while state["stage"] != "EXIT":
        try:
            user_text = input("You: ")
        except (KeyboardInterrupt, EOFError):
            print(f"\n{BOT_NAME}: Chat ended. Goodbye!")
            break

        if not user_text.strip():
            print(f"{BOT_NAME}: Please type something so I can help.")
            continue

        reply, state = get_reply(user_text, state, faqs)
        print(f"{BOT_NAME}: {reply}")


if __name__ == "__main__":
    main()
