"""Q16: Two sum, with specified tie-breaking.
Complexity: Expected O(n) time and O(n) memory for the dictionary solution;
the baseline uses O(n^2) time and O(1) extra memory.
Lesson: Overwriting an earlier duplicate index breaks the smallest-i rule.
"""


def two_sum(nums, target):
    earliest = {}
    for j, value in enumerate(nums):
        complement = target - value
        if complement in earliest:
            return [earliest[complement], j]
        earliest.setdefault(value, j)
    return []


def two_sum_baseline(nums, target):
    for j in range(len(nums)):
        for i in range(j):
            if nums[i] + nums[j] == target:
                return [i, j]
    return []


# Run this file to see an example. Change the sample input to practice.
if __name__ == "__main__":
    nums = [2, 7, 11, 15]
    target = 9
    print("Input:", nums, "target =", target)
    print("Output:", two_sum(nums, target))
