"""Q4: Second-largest distinct value.
Lesson: A repeated maximum does not count as the second-largest value.
"""


def second_largest(nums):
    largest = second = None
    for value in nums:
        if largest is None or value > largest:
            second, largest = largest, value
        elif value != largest and (second is None or value > second):
            second = value
    return second


# Run this file to see an example. Change the sample input to practice.
if __name__ == "__main__":
    nums = [7, 7, 4, 2]
    print("Input:", nums)
    print("Output:", second_largest(nums))
