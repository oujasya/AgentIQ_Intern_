"""Q7: Palindrome.
Lesson: Punctuation must be removed before comparing the two directions.
"""


def is_palindrome(text):
    cleaned = "".join(char.lower() for char in text if char.isalnum())
    return cleaned == cleaned[::-1]


# Run this file to see an example. Change the sample input to practice.
if __name__ == "__main__":
    text = "A man, a plan, a canal: Panama!"
    print("Input:", text)
    print("Output:", is_palindrome(text))
