from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer
import os
import nltk
import re
import random
from nltk.corpus import wordnet as wn
from nltk.stem import WordNetLemmatizer

# Download NLTK data if not already present
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

# Ensure wordnet is available for simple synonym-based paraphrasing
try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')
    nltk.download('omw-1.4')

# Create a new chatbot instance
default_response = "Sorry, I don't understand. Could you rephrase?"

chatbot = ChatBot(
    'MyBot',
    storage_adapter='chatterbot.storage.SQLStorageAdapter',
    logic_adapters=[
        {
            'import_path': 'chatterbot.logic.BestMatch',
            'default_response': default_response,
            'maximum_similarity_threshold': 0.5,
        },
        'chatterbot.logic.TimeLogicAdapter',
    ],
    database_uri='sqlite:///database.sqlite3',
    read_only=True,
)

import sqlite3

# Train the chatbot with the English corpus if not already trained
trainer = ChatterBotCorpusTrainer(chatbot)

def ensure_trained(db_path='database.sqlite3', min_statements=10):
    try:
        # If database file doesn't exist, train
        if not os.path.exists(db_path):
            print("Training chatbot: database not found, training now...")
            trainer.train('chatterbot.corpus.english')
            return

        # If database exists, check how many statements are stored
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT count(*) FROM statement")
        count = cur.fetchone()[0]
        cur.close()
        conn.close()

        if count < min_statements:
            print(f"Training chatbot: only {count} statements found, training now...")
            trainer.train('chatterbot.corpus.english')
        else:
            print(f"Database already trained with {count} statements.")
    except Exception as e:
        err = str(e).lower()
        # If the statements table doesn't exist or DB can't be opened, train the corpora
        if 'no such table' in err or 'unable to open database file' in err:
            print("Training chatbot: DB missing or uninitialized, training now...")
            try:
                trainer.train('chatterbot.corpus.english')
            except Exception as te:
                print(f"Training error: {te}")
        else:
            print(f"Training error: {e}")

# Allow an optional retrain/reset of the DB via --retrain
import argparse

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('--retrain', action='store_true', help='Delete database and retrain from the ChatterBot corpus')
args, _ = parser.parse_known_args()

if args.retrain:
    if os.path.exists('database.sqlite3'):
        try:
            os.remove('database.sqlite3')
            print('Existing database removed. Rebuilding and retraining...')
        except Exception as e:
            print(f'Could not remove database: {e}')
    ensure_trained()
else:
    ensure_trained()

# Simple paraphrase/rephrasing helpers to try related questions
contractions = {
    "what's": 'what is',
    "who's": 'who is',
    "i'm": 'i am',
    "i've": 'i have',
    "can't": 'can not',
    "don't": 'do not',
    "you're": 'you are',
}

def normalize_text(s: str) -> str:
    s = s.replace('’', "'").strip().lower()
    for k, v in contractions.items():
        s = s.replace(k, v)
    s = re.sub(r'[^\w\s]', '', s)
    for f in ['please', 'could you', 'can you', 'would you', 'tell me', 'could you please']:
        s = s.replace(f, '')
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def generate_paraphrases(text: str, max_paraphrases: int = 8):
    tokens = text.split()
    lemmatizer = WordNetLemmatizer()
    paraphrases = []
    for i, word in enumerate(tokens):
        lem = lemmatizer.lemmatize(word)
        synonyms = []
        try:
            for syn in wn.synsets(lem):
                for l in syn.lemmas():
                    name = l.name().replace('_', ' ').lower()
                    if name != word and ' ' not in name and name not in synonyms:
                        synonyms.append(name)
                if len(synonyms) >= 2:
                    break
        except Exception:
            pass
        for syn in synonyms[:2]:
            new = tokens.copy()
            new[i] = syn
            parap = ' '.join(new)
            if parap != text and parap not in paraphrases:
                paraphrases.append(parap)
        if len(paraphrases) >= max_paraphrases:
            break
    random.shuffle(paraphrases)
    return paraphrases[:max_paraphrases]

def get_best_response(user_text: str, primary_threshold: float = 0.5, secondary_threshold: float = 0.4):
    # Normalize early for quick rule checks
    normalized = normalize_text(user_text)

    # Quick special-case: time queries
    if re.search(r"\btime\b", normalized) or re.search(r"\bwhat time\b", normalized) or re.search(r"\bcurrent time\b", normalized) or re.search(r"\btime now\b", normalized):
        try:
            from datetime import datetime
            now = datetime.now().strftime('%H:%M:%S')
            return f'The current time is {now}', 1.0
        except Exception:
            return default_response, 0.0

    # Quick special-case: user wellbeing responses (e.g., "am good", "i'm fine")
    wellbeing_patterns = [
        r"\b(i am|i'm|im|am)\s+(good|fine|doing well|okay|ok|well)\b",
        r"\b(fine|good|okay|ok|doing well|great)\b",
    ]
    for pat in wellbeing_patterns:
        if re.search(pat, normalized):
            replies = [
                "Good to hear!",
                "Nice — glad you're doing well!",
                "Excellent — how can I help you today?",
            ]
            return random.choice(replies), 1.0

    # Try original text via the chatbot model
    resp = chatbot.get_response(user_text)
    try:
        conf = float(resp.confidence)
    except Exception:
        conf = 0.0
    resp_text = str(resp).strip()
    if conf >= primary_threshold and resp_text.lower() != user_text.strip().lower():
        return resp_text, conf

    # Try normalized form and paraphrases
    # normalized already computed above

    # Quick special-case: compliments/acknowledgements after jokes (e.g., "nice joke")
    try:
        low = normalized.lower()
    except Exception:
        low = normalized

    if any(p in low for p in ['nice joke', 'good joke', 'good one', 'that was funny', 'thanks for the joke', 'thanks', 'thank you']) or re.search(r'\b(haha|lol|funny|nice one)\b', low):
        replies = [
            "Glad you liked it!",
            "Happy to make you laugh!",
            "Thanks — want another joke?",
            "You're welcome!",
        ]
        return random.choice(replies), 1.0

    candidates = [normalized]
    candidates.extend(generate_paraphrases(normalized, max_paraphrases=8))

    best_text = resp_text
    best_conf = conf
    for cand in candidates:
        r = chatbot.get_response(cand)
        try:
            c_conf = float(r.confidence)
        except Exception:
            c_conf = 0.0
        c_text = str(r).strip()
        if c_text.lower() == user_text.strip().lower():
            continue
        if c_conf > best_conf:
            best_conf = c_conf
            best_text = c_text
            if best_conf >= primary_threshold:
                break

    if best_conf >= secondary_threshold:
        return best_text, best_conf

    return default_response, best_conf

def run_chatbot():
    print("Hello! I am an advanced chatbot. Type 'bye' to exit.")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["bye", "exit", "quit"]:
            print("Chatbot: Goodbye!")
            break
        response_text, confidence = get_best_response(user_input)
        print(f"Chatbot: {response_text}")

if __name__ == "__main__":
    run_chatbot()
