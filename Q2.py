"""Q2: Sum digits.
Lesson: Integer division is needed; ordinary division produces a float.
"""


def digit_sum(n):
    n = abs(n)
    total = 0
    while n:
        total += n % 10
        n //= 10
    return total


def digit_sum_string(n):
    return sum(int(character) for character in str(abs(n)))


# Run this file to see an example. Change the sample input to practice.
if __name__ == "__main__":
    n = -502
    print("Input:", n)
    print("Output:", digit_sum(n))
