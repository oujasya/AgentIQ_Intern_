"""Q18: Validate brackets.
Complexity: O(n) time and O(n) worst-case memory for nested openings.
Lesson: Equal opening and closing counts do not imply correct nesting.
"""


def valid_brackets(text):
    matching = {')': '(', ']': '[', '}': '{'}
    stack = []
    for char in text:
        if char in "([{":
            stack.append(char)
        elif not stack or stack.pop() != matching[char]:
            return False
    return not stack


# Run this file to see an example. Change the sample input to practice.
if __name__ == "__main__":
    text = "([]){}"
    print("Input:", text)
    print("Output:", valid_brackets(text))
