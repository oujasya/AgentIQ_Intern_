"""Q13: Distinct sorted values.
Complexity: O(n) time and O(u) output memory for u distinct values.
Lesson: Check whether the result is empty before accessing its last element.
"""


def unique_sorted(nums):
    result = []
    for value in nums:
        if not result or result[-1] != value:
            result.append(value)
    return result


# Run this file to see an example. Change the sample input to practice.
if __name__ == "__main__":
    nums = [1, 1, 2, 2, 4]
    print("Input:", nums)
    print("Output:", unique_sorted(nums))
