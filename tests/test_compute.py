import io
import os
import subprocess
import sys
import unittest

import compute

SCRIPT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "compute.py")


# run compute.main with in-memory streams and capture the output
def run(args, text):
    out, err = io.StringIO(), io.StringIO()
    code = compute.main(args, io.StringIO(text), out, err)
    return code, out.getvalue().splitlines(), err.getvalue()


class ComputeTests(unittest.TestCase):

    # the main example from the readme
    def test_readme_example(self):
        text = "19.0\n0.0\n1000\n1001.5\n20000\n25000000.0\n"
        code, lines, _ = run(["1000", "20000000"], text)
        self.assertEqual(code, 0)
        self.assertEqual(lines, ["0.0", "0.0", "0.0", "1.5", "19000.0",
                                 "19980998.5", "20000000.0"])

    # each row of the threshold table from the readme
    def test_threshold_table(self):
        cases = [("0.0", "0.0", "0.0"), ("10.0", "0.0", "10.0"),
                 ("0.0", "10.0", "0.0"), ("5.0", "10.0", "0.0"),
                 ("10.0", "5.0", "5.0"), ("20.0", "5.0", "15.0")]
        for value, threshold, expected in cases:
            _, lines, _ = run([threshold, "1000"], value + "\n")
            self.assertEqual(lines[0], expected, (value, threshold))

    # examples from the readme, cap hit on the fourth value
    def test_limit_100(self):
        _, lines, _ = run(["0", "100"], "0.0\n10.0\n50.0\n50.0\n10.0\n20.0\n")
        self.assertEqual(lines, ["0.0", "10.0", "50.0", "40.0", "0.0", "0.0", "100.0"])

    # a zero limit means every output is zero
    def test_limit_zero(self):
        _, lines, _ = run(["0", "0"], "0.0\n10.0\n20.0\n")
        self.assertEqual(lines, ["0.0", "0.0", "0.0", "0.0"])

    # no input lines should still print a total of zero
    def test_empty_input(self):
        code, lines, _ = run(["10", "100"], "")
        self.assertEqual(code, 0)
        self.assertEqual(lines, ["0.0"])

    # unline floats, decimal sums should stay exact
    def test_no_float_drift(self):
        _, lines, _ = run(["0", "1000"], "0.1\n" * 10)
        self.assertEqual(lines[-1], "1.0")

    # max size inputs and limit, 100 lines
    def test_large_values(self):
        _, lines, _ = run(["0", "1000000000"], "1000000000.0\n" * 100)
        self.assertEqual(lines[0], "1000000000.0")
        self.assertEqual(lines[1], "0.0")
        self.assertEqual(lines[-1], "1000000000.0")
        self.assertEqual(len(lines), 101)

    # handles line breaks, blank lines and extra spaces
    def test_messy_whitespace(self):
        _, lines, _ = run(["0", "100"], " 5\r\n\n10.5 \r\n")
        self.assertEqual(lines, ["5.0", "10.5", "15.5"])

    # bad arguments exit with code 2 and print nothing 
    def test_bad_args(self):
        for args in (["1"], ["a", "1"], ["-1", "5"], ["1", "1000000000.1"], ["nan", "1"]):
            code, lines, err = run(args, "1\n")
            self.assertEqual(code, 2, args)
            self.assertEqual(lines, [])
            self.assertTrue(err)

    # a bad input line exits with code 1 and prints nothing
    def test_bad_input_line(self):
        code, lines, _ = run(["0", "100"], "1\nabc\n2\n")
        self.assertEqual(code, 1)
        self.assertEqual(lines, [])

    # run the script end to end 
    def test_cli(self):
        result = subprocess.run([sys.executable, SCRIPT, "1000", "20000000"],
                                input=b"1001.5\n25000000\n", stdout=subprocess.PIPE)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.decode().split(), ["1.5", "19999998.5", "20000000.0"])


if __name__ == "__main__":
    unittest.main()
