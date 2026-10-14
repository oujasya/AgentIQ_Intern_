"""Q10: Run-length encoding.
Lesson: The last run needs explicit handling; counts may contain multiple digits.
"""


def run_length_encode(text):
    if not text:
        return ""
    parts = []
    previous, count = text[0], 1
    for char in text[1:]:
        if char == previous:
            count += 1
        else:
            parts.append(previous + str(count))
            previous, count = char, 1
    parts.append(previous + str(count))
    return "".join(parts)


# Run this file to see an example. Change the sample input to practice.
if __name__ == "__main__":
    text = "aaabbc"
    print("Input:", text)
    print("Output:", run_length_encode(text))
