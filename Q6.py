"""Q6: Normalize words.
Lesson: split(' ') does not handle arbitrary whitespace correctly.
"""


def normalize_words(text):
    return " ".join(text.split()).lower()


# Run this file to see an example. Change the sample input to practice.
if __name__ == "__main__":
    text = "  SAP\tSupport  "
    print("Input:", repr(text))
    print("Output:", normalize_words(text))
