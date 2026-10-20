"""Hangman Word Guessing Game (Console)

Concepts used: string manipulation, sets, loops, control flow, functions, file I/O.
Run with:  python hangman.py
Optional:  put a words.txt (one word per line) in the same folder to use a bigger word list.
"""

import os
import random

MAX_MISTAKES = 6

# Built-in fallback list, used if words.txt is not found
DEFAULT_WORDS = [
    "python", "variable", "function", "program", "keyboard", "network",
    "developer", "algorithm", "database", "terminal", "compiler", "library",
    "internet", "software", "hardware", "debugging", "iteration", "boolean",
    "dictionary", "framework", "portfolio", "challenge", "elephant", "mountain",
]

# ASCII gallows: index = number of wrong guesses (0 to 6)
STAGES = [
    """
      +---+
      |   |
          |
          |
          |
          |
    =========
    """,
    """
      +---+
      |   |
      O   |
          |
          |
          |
    =========
    """,
    """
      +---+
      |   |
      O   |
      |   |
          |
          |
    =========
    """,
    """
      +---+
      |   |
      O   |
     /|   |
          |
          |
    =========
    """,
    """
      +---+
      |   |
      O   |
     /|\\  |
          |
          |
    =========
    """,
    """
      +---+
      |   |
      O   |
     /|\\  |
     /    |
          |
    =========
    """,
    """
      +---+
      |   |
      O   |
     /|\\  |
     / \\  |
          |
    =========
    """,
]


def load_words(filename="words.txt"):
    """Load words from a text file; fall back to the built-in list."""
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            words = [w.strip().lower() for w in f if w.strip().isalpha() and len(w.strip()) >= 4]
        if words:
            return words
    return DEFAULT_WORDS


def choose_word(words):
    return random.choice(words)


def masked_word(secret, guessed):
    """Return e.g. '_ a _ h _ o n' based on the correctly guessed letters."""
    return " ".join(ch if ch in guessed else "_" for ch in secret)


def get_guess(guessed):
    """Ask for one valid, new letter."""
    while True:
        guess = input("Guess a letter: ").strip().lower()
        if len(guess) != 1 or not guess.isalpha():
            print("Please enter a single letter (a-z).")
        elif guess in guessed:
            print(f"You already guessed '{guess}'. Try another letter (no penalty).")
        else:
            return guess


def show_status(secret, guessed, wrong, mistakes):
    print(STAGES[mistakes])
    print("Word:", masked_word(secret, guessed))
    print("Wrong letters:", " ".join(sorted(wrong)) if wrong else "-")
    print(f"Attempts left: {MAX_MISTAKES - mistakes}\n")


def play_round(words):
    secret = choose_word(words)
    guessed = set()   # every letter tried (right or wrong)
    wrong = set()     # only the wrong ones
    mistakes = 0

    print("\n=== HANGMAN ===")
    print(f"The word has {len(secret)} letters. You have {MAX_MISTAKES} wrong guesses.")

    while mistakes < MAX_MISTAKES and not set(secret) <= guessed:
        show_status(secret, guessed, wrong, mistakes)
        guess = get_guess(guessed)
        guessed.add(guess)

        if guess in secret:
            print(f"Good job! '{guess}' is in the word.")
        else:
            wrong.add(guess)
            mistakes += 1
            print(f"Sorry, '{guess}' is not in the word.")

    print(STAGES[mistakes])
    if set(secret) <= guessed:
        print("*****************************")
        print("*   VICTORY! You got it!    *")
        print("*****************************")
    else:
        print("-----------------------------")
        print("-   DEFEAT! You were hanged -")
        print("-----------------------------")
    print(f"The word was: {secret.upper()}")


def main():
    words = load_words()
    while True:
        play_round(words)
        again = input("\nPlay again? (y/n): ").strip().lower()
        if again != "y":
            print("Thanks for playing!")
            break


if __name__ == "__main__":
    main()
