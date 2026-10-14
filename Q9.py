"""Q9: Anagrams.
Lesson: Sets lose repeated-letter counts and cannot establish anagrams.
"""
from collections import Counter


def are_anagrams(a, b):
    return Counter(a.replace(" ", "").lower()) == Counter(b.replace(" ", "").lower())


# Run this file to see an example. Change the sample input to practice.
if __name__ == "__main__":
    a = "Dormitory"
    b = "Dirty room"
    print("Inputs:", a, "and", b)
    print("Output:", are_anagrams(a, b))
