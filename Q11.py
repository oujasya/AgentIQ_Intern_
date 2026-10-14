"""Q11: Move zeros.
Complexity: O(n) time and O(n) memory for the returned list.
Lesson: Removing items while iterating can skip values and mutate the input.
"""


def move_zeros(nums):
    nonzero = [value for value in nums if value != 0]
    return nonzero + [0] * (len(nums) - len(nonzero))


# Run this file to see an example. Change the sample input to practice.
if __name__ == "__main__":
    nums = [0, 1, 0, 3, 12]
    print("Input:", nums)
    print("Output:", move_zeros(nums))
