import json

class SaneTokenizer:
    def __init__(self):
        # Start with a base vocabulary of characters
        self.vocab = {
            "tokenization": 1001,
            "python": 1002,
            "coding": 1003,
            "is": 1004,
            "the": 1005,
            "process": 1006
        }
        # Reverse lookup for decoding
        self.id_to_token = {v: k for k, v in self.vocab.items()}
        
    def tokenize(self, text):
        # 1. Clean and split by whitespace/punctuation
        raw_words = text.lower().strip().split()
        final_tokens = []

        for word in raw_words:
            # Check if the "sane" word exists in our vocab
            if word in self.vocab:
                final_tokens.append({
                    "type": "Sane Token",
                    "word": word,
                    "id": self.vocab[word]
                })
            else:
                # 2. "Diff" the random word into individual characters
                char_ids = [ord(char) for char in word]
                final_tokens.append({
                    "type": "Random/Diffed",
                    "word": word,
                    "breakdown": list(word),
                    "ids": char_ids
                })
        return final_tokens

# --- Interactive App ---
tokenizer = SaneTokenizer()

print("--- The Sane vs. Random Tokenizer ---")
print("Known words: tokenization, python, coding, is, the, process")
print("Type 'quit' to stop.\n")

while True:
    user_input = input("Enter text: ")
    if user_input.lower() == 'quit':
        break

    results = tokenizer.tokenize(user_input)

    print("\nProcessing Results:")
    print("-" * 30)
    for res in results:
        if res["type"] == "Sane Token":
            print(f"✅ '{res['word']}' -> Recognised as Token ID: {res['id']}")
        else:
            # This handles your 'efa' or 'diff' examples
            print(f"❓ '{res['word']}' -> Unknown! Diffing into: {res['breakdown']} (IDs: {res['ids']})")
    print("-" * 30 + "\n")