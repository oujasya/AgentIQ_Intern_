"""At least five normal/boundary assertions for each of Q1-Q25.
Run from this directory: python -m unittest -v
"""
import copy
import importlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from Q21 import validate_records
from Q22 import deduplicate
from Q23 import summarize
from Q24 import find_findings
from Q25 import build_report

ROOT = Path(__file__).resolve().parent


def row(**changes):
    result = {"id": "X1", "source": "salesforce", "status": "open", "category": "access",
              "created_at": "2026-09-22", "owner_changes": 0}
    result.update(changes)
    return result


def fixture():
    return json.loads((ROOT / "records.json").read_text(encoding="utf-8"))


# Each tuple contains the function's argument tuple and the exact expected return.
CASES = {
    1: ("fizz_buzz", [((0,), []), ((1,), ["1"]), ((3,), ["1", "2", "Fizz"]),
         ((5,), ["1", "2", "Fizz", "4", "Buzz"]),
         ((15,), ["1", "2", "Fizz", "4", "Buzz", "Fizz", "7", "8", "Fizz", "Buzz", "11", "Fizz", "13", "14", "FizzBuzz"])]),
    2: ("digit_sum", [((0,), 0), ((-502,), 7), ((8,), 8), ((999,), 27), ((12000,), 3)]),
    3: ("is_prime", [((-7,), False), ((0,), False), ((1,), False), ((2,), True), ((29,), True), ((49,), False), ((1000000,), False)]),
    4: ("second_largest", [(([],), None), (([4],), None), (([5, 5],), None),
         (([-9, -2, -5],), -5), (([7, 7, 4, 2],), 4), (([1, 2, 3],), 2)]),
    5: ("missing_number", [(([1, 2],), 0), (([0, 1],), 2), (([0, 2],), 1), (([],), 0), (([3, 0, 1],), 2)]),
    6: ("normalize_words", [(("",), ""), (("   \t\n",), ""), ((" SAP\tSupport ",), "sap support"),
         (("A\nB",), "a b"), (("already clean",), "already clean")]),
    7: ("is_palindrome", [(("",), True), (("!?",), True), (("A man, a plan, a canal: Panama!",), True),
         (("12 21",), True), (("hello",), False), (("0P",), False)]),
    8: ("first_unique_index", [(("",), -1), (("aabb",), -1), (("x",), 0), (("aa bb",), 2), (("aA",), 0), (("swiss",), 1)]),
    9: ("are_anagrams", [(("", ""), True), (("a", "aa"), False), (("aab", "aba"), True),
         (("Dormitory", "Dirty room"), True), (("cat", "car"), False), (("aab", "abb"), False)]),
    10: ("run_length_encode", [(("",), ""), (("a",), "a1"), (("aba",), "a1b1a1"), (("abc",), "a1b1c1"),
          (("a" * 12,), "a12"), (("aaabbc",), "a3b2c1")]),
    11: ("move_zeros", [(([],), []), (([0, 0],), [0, 0]), (([1, 2],), [1, 2]),
          (([0, -1, 0, -2],), [-1, -2, 0, 0]), (([0, 1, 0, 3, 12],), [1, 3, 12, 0, 0])]),
    12: ("rotate_left", [(([], 5), []), (([1, 2], 0), [1, 2]), (([1, 2], 2), [1, 2]),
          (([1, 2, 3, 4], 6), [3, 4, 1, 2]), (([7], 999), [7])]),
    13: ("unique_sorted", [(([],), []), (([1, 1],), [1]), (([1, 2, 4],), [1, 2, 4]),
          (([-3, -3, -1, 0],), [-3, -1, 0]), (([8],), [8])]),
    14: ("merge_sorted", [(([], []), []), (([], [1]), [1]), (([1, 1], [1]), [1, 1, 1]),
          (([1, 3, 5], [2]), [1, 2, 3, 5]), (([-4, -1], [-3, 0]), [-4, -3, -1, 0]),
          (([1, 3, 5], [2, 3, 6]), [1, 2, 3, 3, 5, 6])]),
    15: ("longest_ones", [(([],), 0), (([0, 0],), 0), (([1, 1, 1],), 3),
          (([1, 0, 1, 1],), 2), (([1, 1, 0, 1, 1],), 2)]),
    16: ("two_sum", [(([1, 2], 9), []), (([3, 3], 6), [0, 1]), (([-3, 1, 2], -2), [0, 1]),
          (([1, 2, 3, 4], 5), [1, 2]), (([], 0), []), (([1, 1, 3], 4), [0, 2])]),
    17: ("word_counts", [(("",), {}), (("a  \t b\n",), {"a": 1, "b": 1}),
          (("Login failed login",), {"login": 2, "failed": 1}), (("word",), {"word": 1}), (("a a a",), {"a": 3})]),
    18: ("valid_brackets", [(("",), True), ((")(",), False), (("([]){}",), True), (("((",), False), (("([)]",), False)]),
    19: ("binary_search", [(([], 1), -1), (([7], 7), 0), (([2, 5, 8, 12], 2), 0),
          (([2, 5, 8, 12], 12), 3), (([2, 5], 3), -1), (([2, 5, 8, 12], 8), 2)]),
    20: ("top_k_frequent", [(([], 2), []), (([1], 0), []), (([4, 4, 2], 9), [4, 2]),
          (([4, 4, 2, 2, 3], 2), [2, 4]), (([-2, -1, -1, -2, 0], 2), [-2, -1])]),
}


class CodingTests(unittest.TestCase):
    """One named test method per problem; subtests expose each assertion."""


def make_test(number, function_name, cases):
    def test(self):
        function = getattr(importlib.import_module(f"Q{number}"), function_name)
        for args, expected in cases:
            with self.subTest(args=args):
                original = copy.deepcopy(args)
                self.assertEqual(function(*args), expected)
                self.assertEqual(args, original, "Input values must be preserved")
                if number in (11, 12, 13):
                    self.assertIsNot(function(*args), args[0], "Return a new list")
                if number == 2:
                    self.assertEqual(importlib.import_module("Q2").digit_sum_string(*args), expected)
                if number == 16:
                    self.assertEqual(importlib.import_module("Q16").two_sum_baseline(*args), expected)
    return test


for number, (function_name, cases) in CASES.items():
    setattr(CodingTests, f"test_Q{number:02d}_{function_name}", make_test(number, function_name, cases))


class RecordTests(unittest.TestCase):
    def test_Q21_validate_records(self):
        missing = row()
        del missing["status"]
        invalid_rows = [missing, None, row(id=" \t"), row(created_at="2026-02-30"),
                        row(owner_changes=-1), row(owner_changes=1.5), row(owner_changes=True),
                        row(owner_changes="2"), row(category=""), row(source=[]), row(status="pending"),
                        row(created_at="2026-9-01"), row(created_at="2026-09-01T00:00:00"),
                        row(created_at=20260901)]
        for invalid in invalid_rows:
            with self.subTest(row=invalid):
                result = validate_records([invalid])
                self.assertEqual(result["valid"], [])
                self.assertEqual(result["rejected"][0]["index"], 0)
                self.assertTrue(result["rejected"][0]["reasons"])
        data = fixture()
        before = copy.deepcopy(data)
        result = validate_records(data)
        self.assertEqual(len(result["valid"]), 7)
        self.assertEqual([item["index"] for item in result["rejected"]], [7, 8, 9])
        self.assertEqual(data, before)
        self.assertTrue(all(a is b for a, b in zip(result["valid"], data[:7])))
        self.assertEqual(validate_records([]), {"valid": [], "rejected": []})
        valid = row(id=" X1 ", category=" access ", created_at="2024-02-29")
        self.assertEqual(validate_records([valid])["valid"], [valid])
        multiple = validate_records([{}])["rejected"][0]["reasons"]
        self.assertEqual(len(multiple), 6)

    def test_Q22_deduplicate(self):
        a, b = row(), row(source="jira")
        changed = row(owner_changes=9)
        cases = [([], [], 0), ([a, b], [a, b], 0), ([a, a, a], [a], 2),
                 ([a, changed], [a], 1), ([a, row(id="Y2")], [a, row(id="Y2")], 0)]
        for data, expected, removed in cases:
            with self.subTest(data=data):
                before = copy.deepcopy(data)
                self.assertEqual(deduplicate(data), {"records": expected, "duplicates_removed": removed})
                self.assertEqual(data, before)
        result = deduplicate(validate_records(fixture())["valid"])
        self.assertEqual(len(result["records"]), 6)
        self.assertEqual(result["duplicates_removed"], 1)
        self.assertEqual(result["records"][0]["owner_changes"], 4)
        self.assertIs(deduplicate([a])["records"][0], a)

    def test_Q23_summarize(self):
        empty = summarize([])
        self.assertEqual(empty, {"total": 0, "by_status": {"open": 0, "closed": 0},
            "by_source": {"salesforce": 0, "jira": 0, "servicenow": 0}, "by_category": {}})
        self.assertEqual(summarize([row()])["by_source"], {"salesforce": 1, "jira": 0, "servicenow": 0})
        self.assertEqual(summarize([row(), row(id="Y2")])["by_status"], {"open": 2, "closed": 0})
        self.assertEqual(summarize([row(), row(category="billing"), row(category="other")])["by_category"],
                         {"access": 1, "billing": 1, "other": 1})
        self.assertEqual(summarize([row(), row(source="jira")])["total"], 2)
        result = summarize(deduplicate(validate_records(fixture())["valid"])["records"])
        self.assertEqual(result, {"total": 6, "by_status": {"open": 4, "closed": 2},
            "by_source": {"salesforce": 2, "jira": 2, "servicenow": 2}, "by_category": {"access": 4, "billing": 2}})

    def test_Q24_find_findings(self):
        reference = "2026-09-30"
        self.assertEqual(find_findings([], reference), {"aging": [], "handoff": []})
        self.assertEqual(find_findings([row(created_at="2026-09-23")], reference)["aging"], [])
        self.assertEqual(find_findings([row(created_at="2026-09-22")], reference)["aging"][0]["observed_value"], 8)
        self.assertEqual(find_findings([row(owner_changes=3)], reference)["handoff"], [])
        self.assertEqual(find_findings([row(owner_changes=4)], reference)["handoff"][0]["observed_value"], 4)
        self.assertEqual(find_findings([row(status="closed", created_at="2026-01-01")], reference)["aging"], [])
        self.assertEqual(find_findings([row(created_at="2026-10-01")], reference)["aging"], [])
        self.assertEqual(len(find_findings([row(status="closed", owner_changes=4)], reference)["handoff"]), 1)
        records = deduplicate(validate_records(fixture())["valid"])["records"]
        result = find_findings(records, reference)
        self.assertEqual([(f["source"], f["id"], f["observed_value"]) for f in result["aging"]],
                         [("salesforce", "A1", 29), ("salesforce", "C3", 8)])
        self.assertEqual([(f["source"], f["id"], f["observed_value"]) for f in result["handoff"]],
                         [("salesforce", "A1", 4), ("jira", "D4", 5)])
        for kind, threshold in (("aging", 7), ("handoff", 3)):
            for finding in result[kind]:
                self.assertEqual(set(finding), {"source", "id", "observed_value", "threshold", "reason"})
                self.assertEqual(finding["threshold"], threshold)
                self.assertTrue(finding["reason"])

    def test_Q25_cli_and_pipeline(self):
        # Invoke the real entry point so exit codes, errors and output preservation are tested.
        with tempfile.TemporaryDirectory(dir=ROOT, prefix=".test-") as directory:
            input_path = Path(directory) / "input.json"
            output_path = Path(directory) / "output.json"
            for data in (fixture(), [], [None, {}]):
                with self.subTest(valid_input=data):
                    input_path.write_text(json.dumps(data), encoding="utf-8")
                    output_path.write_text("old report", encoding="utf-8")
                    completed = subprocess.run([sys.executable, str(ROOT / "Q25.py"), str(input_path), str(output_path)],
                                               capture_output=True, text=True)
                    self.assertEqual(completed.returncode, 0, completed.stderr)
                    result = json.loads(output_path.read_text(encoding="utf-8"))
                    self.assertEqual(result, build_report(data))
                    self.assertEqual(result["input_count"], result["valid_count"] + result["rejected_count"])
                    self.assertEqual(result["summary"]["total"], result["valid_count"] - result["duplicates_removed"])
                    for key in ("by_source", "by_status"):
                        self.assertEqual(sum(result["summary"][key].values()), result["summary"]["total"])
            for bad in (None, "{broken", '{}', '"text"', 'null'):
                with self.subTest(invalid_input=bad):
                    if bad is None:
                        input_path.unlink(missing_ok=True)
                    else:
                        input_path.write_text(bad, encoding="utf-8")
                    sentinel = b"existing output must survive\x00\n"
                    output_path.write_bytes(sentinel)
                    completed = subprocess.run([sys.executable, str(ROOT / "Q25.py"), str(input_path), str(output_path)],
                                               capture_output=True, text=True)
                    self.assertNotEqual(completed.returncode, 0)
                    self.assertIn("Error:", completed.stderr)
                    self.assertEqual(output_path.read_bytes(), sentinel)
            # A destination directory cannot be replaced by a regular report file.
            input_path.write_text("[]", encoding="utf-8")
            protected_directory = Path(directory) / "protected"
            protected_directory.mkdir()
            completed = subprocess.run([sys.executable, str(ROOT / "Q25.py"), str(input_path), str(protected_directory)],
                                       capture_output=True, text=True)
            self.assertNotEqual(completed.returncode, 0)
            self.assertTrue(protected_directory.is_dir())
            self.assertEqual(list(Path(directory).glob(".report-*.tmp")), [])
        result = build_report(fixture())
        self.assertEqual([result[k] for k in ("input_count", "valid_count", "rejected_count", "duplicates_removed")], [10, 7, 3, 1])
        self.assertEqual(result["summary"]["total"], 6)


if __name__ == "__main__":
    unittest.main(verbosity=2)
