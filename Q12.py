"""Q12: Rotate left.
Complexity: O(n) time and O(n) memory; slicing returns a new list.
Lesson: A rotation by the list length leaves values in the same order.
"""


def rotate_left(nums, k):
    if not nums:
        return []
    k %= len(nums)
    return nums[k:] + nums[:k]


# Run this file to see an example. Change the sample input to practice.
if __name__ == "__main__":
    nums = [1, 2, 3, 4]
    k = 6
    print("Input:", nums, "k =", k)
    print("Output:", rotate_left(nums, k))
