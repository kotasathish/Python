from chatterbot import ChatBot
from chatterbot.trainers import ChatterBotCorpusTrainer
import os
import nltk

# Download NLTK data if not already present
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

# Create a new chatbot instance
chatbot = ChatBot('MyBot',
                  storage_adapter='chatterbot.storage.SQLStorageAdapter',
                  logic_adapters=[
                      'chatterbot.logic.BestMatch',
                      'chatterbot.logic.TimeLogicAdapter',
                  ],
                  database_uri='sqlite:///database.sqlite3')

# Train the chatbot with the English corpus if not already trained
trainer = ChatterBotCorpusTrainer(chatbot)
try:
    if not os.path.exists('database.sqlite3'):
        trainer.train('chatterbot.corpus.english')
except Exception as e:
    print(f"Training error: {e}")

def run_chatbot():
    print("Hello! I am an advanced chatbot. Type 'bye' to exit.")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["bye", "exit", "quit"]:
            print("Chatbot: Goodbye!")
            break
        response = chatbot.get_response(user_input)
        print(f"Chatbot: {response}")

if __name__ == "__main__":
    run_chatbot()
