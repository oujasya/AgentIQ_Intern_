"""Q1: FizzBuzz.
"""


def fizz_buzz(n):
    result = []
    for value in range(1, n + 1):
        if value % 15 == 0:
            result.append("FizzBuzz")
        elif value % 3 == 0:
            result.append("Fizz")
        elif value % 5 == 0:
            result.append("Buzz")
        else:
            result.append(str(value))
    return result


if __name__ == "__main__":
    n = 15
    print("Input:", n)
    print("Output:", fizz_buzz(n))
