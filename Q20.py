"""Q20: Most frequent values.
Complexity: O(n + u log u) time and O(u) memory for u distinct values.
Lesson: Frequency ties need a numeric sort key, not input-order tie-breaking.
"""


def top_k_frequent(nums, k):
    counts = {}
    for num in nums:
        counts[num] = counts.get(num, 0) + 1
    sorted_nums = sorted(counts, key=lambda x: (-counts[x], x))
    return sorted_nums[:k]


# Run this file to see an example. Change the sample input to practice.
if __name__ == "__main__":
    nums = [4, 4, 2, 2, 3]
    k = 2
    print("Input:", nums, "k =", k)
    print("Output:", top_k_frequent(nums, k))
