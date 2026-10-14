"""Q19: Binary search.
Complexity: O(log n) time for nonempty input and O(1) extra memory.
Lesson: Move past the midpoint to avoid repeatedly searching the same range.
"""


def binary_search(nums, target):
    left, right = 0, len(nums) - 1
    while left <= right:
        middle = (left + right) // 2
        if nums[middle] == target:
            return middle
        if nums[middle] < target:
            left = middle + 1
        else:
            right = middle - 1
    return -1


# Run this file to see an example. Change the sample input to practice.
if __name__ == "__main__":
    nums = [2, 5, 8, 12]
    target = 8
    print("Input:", nums, "target =", target)
    print("Output:", binary_search(nums, target))
