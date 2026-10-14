"""Q14: Merge sorted lists.
Complexity: O(n + m) time and O(n + m) output memory.
Lesson: Equal values must both survive the merge.
"""


def merge_sorted(a, b):
    result = []
    i = j = 0
    while i < len(a) and j < len(b):
        if a[i] <= b[j]:
            result.append(a[i])
            i += 1
        else:
            result.append(b[j])
            j += 1
    result.extend(a[i:])
    result.extend(b[j:])
    return result


# Run this file to see an example. Change the sample input to practice.
if __name__ == "__main__":
    a = [1, 3, 5]
    b = [2, 3, 6]
    print("Inputs:", a, "and", b)
    print("Output:", merge_sorted(a, b))
