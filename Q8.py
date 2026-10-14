"""Q8: First unique character index.
Lesson: Return an index in the original string, not in a cleaned string.
"""
from collections import Counter


def first_unique_index(text):
    counts = Counter(text)
    for index, char in enumerate(text):
        if counts[char] == 1:
            return index
    return -1


# Run this file to see an example. Change the sample input to practice.
if __name__ == "__main__":
    text = "swiss"
    print("Input:", text)
    print("Output:", first_unique_index(text))
