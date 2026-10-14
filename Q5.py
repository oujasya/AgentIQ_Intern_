"""Q5: Missing number.
Lesson: The upper bound is the input length, including for an empty list.
"""


def missing_number(nums):
    n = len(nums)
    return n * (n + 1) // 2 - sum(nums)


# Run this file to see an example. Change the sample input to practice.
if __name__ == "__main__":
    nums = [3, 0, 1]
    print("Input:", nums)
    print("Output:", missing_number(nums))
