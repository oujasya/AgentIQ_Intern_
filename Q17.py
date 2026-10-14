"""Q17: Count words.
Complexity: O(c) time and O(c) memory where c is the text length, including
split strings and dictionary keys. Return an ordinary dictionary.
Lesson: Repeated whitespace should not produce empty-word entries.
"""
from collections import Counter


def word_counts(text):
    return dict(Counter(text.lower().split()))


# Run this file to see an example. Change the sample input to practice.
if __name__ == "__main__":
    text = "Login failed login"
    print("Input:", text)
    print("Output:", word_counts(text))
