"""Q3: Prime check.
Lesson: Perfect squares require checking the square-root divisor itself.
"""
from math import isqrt


def is_prime(n):
    if n < 2:
        return False
    for divisor in range(2, isqrt(n) + 1):
        if n % divisor == 0:
            return False
    return True


# Run this file to see an example. Change the sample input to practice.
if __name__ == "__main__":
    n = 29
    print("Input:", n)
    print("Output:", is_prime(n))
