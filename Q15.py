"""Q15: Longest run of ones.
Complexity: O(n) time and O(1) extra memory.
Lesson: Update the maximum during the loop, not only when a zero arrives.
"""


def longest_ones(bits):
    current = best = 0
    for bit in bits:
        current = current + 1 if bit == 1 else 0
        best = max(best, current)
    return best


# Run this file to see an example. Change the sample input to practice.
if __name__ == "__main__":
    bits = [1, 1, 0, 1, 1, 1]
    print("Input:", bits)
    print("Output:", longest_ones(bits))
