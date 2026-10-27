# Line 1:  Import time for measuring latency of agent runs.
import time


# Line 2:  Define the Evaluator class that scores agent outputs against expected criteria.
class Evaluator:
    # Line 3:  Initialize with a list of test case definitions and scoring thresholds.
    def __init__(self, latency_budget=10.0):
        # Line 4:  Store the maximum allowed execution time (seconds) for a single agent run.
        self.latency_budget = latency_budget
        # Line 5:  Store test cases as a list of dicts (each defines input + expected criteria).
        self.test_cases = []
        # Line 6:  Store the results from the most recent evaluation run.
        self.last_results = []

    # Line 7:  Add a test case to the evaluator's suite.
    def add_test_case(
        self, name, input_text, expected_keywords=None, expected_tools=None
    ):
        # Line 8:  Create a test case dict with all scoring criteria.
        tc = {
            "name": name,  # Line 9:  Human-readable name for reporting.
            "input": input_text,  # Line 10: The goal/input to feed the agent.
            "expected_keywords": expected_keywords
            or [],  # Line 11: Words that must appear in the output.
            "expected_tools": expected_tools
            or [],  # Line 12: Tools that should have been called.
        }
        # Line 13:  Append this test case to our suite.
        self.test_cases.append(tc)

    # Line 14:  Run all test cases against the provided agent; returns a scored report.
    def run(self, agent):
        # Line 15:  Initialize results list for this evaluation run.
        results = []
        # Line 16:  Iterate over each defined test case to execute and score it.
        for tc in self.test_cases:
            # Line 17:  Record the start time for this individual test case execution.
            t_start = time.time()
            # Line 18:  Run the agent on this test case's input and capture the output.
            try:
                # Line 19:  Call the agent's run method with the test input.
                output = agent.run(tc["input"])
            except Exception as e:
                # Line 20:  If the agent crashed, record it as a failure with zero score.
                output = f"AGENT CRASHED: {e}"
            # Line 21:  Calculate elapsed time for this test case.
            elapsed = time.time() - t_start
            # Line 22:  Score the output against all criteria and get a composite score (0-1).
            score = self._score(output, tc, elapsed)
            # Line 23:  Store the result for this test case.
            results.append(
                {
                    "name": tc["name"],  # Line 24:  Test case name for reporting.
                    "score": score,  # Line 25:  Composite score (0.0 to 1.0).
                    "elapsed": elapsed,  # Line 26:  Execution time in seconds.
                    "output": output,  # Line 27:  The agent's actual output text.
                    "passed": score
                    >= 0.5,  # Line 28:  Binary pass/fail (threshold at 50%).
                }
            )
        # Line 29:  Store the results for later access (e.g., by trace logger or main script).
        self.last_results = results
        # Line 30:  Return the full results list.
        return results

    # Line 31:  Score a single output against a test case's criteria; returns composite score 0-1.
    def _score(self, output, tc, elapsed):
        # Line 32:  Initialize component scores (each contributes equally to the final score).
        keyword_score = self._score_keywords(output, tc["expected_keywords"])
        # Line 33:  Score tool-call correctness (did it call the expected tools?).
        tool_score = self._score_tools(output, tc["expected_tools"])
        # Line 34:  Score latency compliance (was it fast enough?).
        latency_score = self._score_latency(elapsed)
        # Line 35:  Compute composite score as the mean of all component scores.
        components = [keyword_score, tool_score, latency_score]
        # Line 36:  Average the component scores to get a single 0-1 metric.
        composite = sum(components) / len(components)
        # Line 37:  Return the clamped composite score (ensure it's between 0 and 1).
        return max(0.0, min(1.0, composite))

    # Line 38:  Score keyword presence: what fraction of expected keywords appear in the output?
    def _score_keywords(self, output, expected_keywords):
        # Line 39:  If no keywords are expected, give full score (nothing to check).
        if not expected_keywords:
            # Line 40:  Return 1.0 when there are no keyword requirements.
            return 1.0
        # Line 41:  Convert output to lowercase for case-insensitive matching.
        output_lower = output.lower()
        # Line 42:  Count how many expected keywords are found in the output.
        found = sum(1 for kw in expected_keywords if kw.lower() in output_lower)
        # Line 43:  Return the fraction of keywords that were found (0.0 to 1.0).
        return found / len(expected_keywords)

    # Line 44:  Score tool-call correctness by checking if expected tool names appear in output/trace.
    def _score_tools(self, output, expected_tools):
        # Line 45:  If no tools are expected, give full score.
        if not expected_tools:
            # Line 46:  Return 1.0 when there are no tool requirements.
            return 1.0
        # Line 47:  Check how many expected tool names appear in the output text.
        found = sum(1 for tool in expected_tools if tool.lower() in output.lower())
        # Line 48:  Return the fraction of expected tools that were mentioned/used.
        return found / len(expected_tools)

    # Line 49:  Score latency compliance: 1.0 if within budget, 0.0 if exceeded.
    def _score_latency(self, elapsed):
        # Line 50:  If execution was within the time budget, full score.
        if elapsed <= self.latency_budget:
            # Line 51:  Return 1.0 for timely execution.
            return 1.0
        # Line 52:  Exceeded budget — return 0.0 (binary: either fast enough or not).
        return 0.0

    # Line 53:  Print a formatted evaluation report to the terminal.
    def print_report(self):
        # Line 54:  Print a header for the evaluation section.
        print(f"\n{'=' * 60}")
        # Line 55:  Print the evaluator title with total test count.
        print(f"  EVALUATOR REPORT ({len(self.last_results)} test cases)")
        # Line 56:  Print a separator line.
        print(f"{'=' * 60}")
        # Line 57:  Track pass/fail counts for the summary line.
        passed = sum(1 for r in self.last_results if r["passed"])
        # Line 58:  Iterate over results to print each test case's score.
        for r in self.last_results:
            # Line 59:  Format the pass/fail indicator with appropriate text.
            status = "PASS" if r["passed"] else "FAIL"
            # Line 60:  Print the result line with name, score percentage, and time.
            print(
                f"  [{status}] {r['name']}: {r['score']*100:.0f}% ({r['elapsed']:.2f}s)"
            )
        # Line 61:  Print the overall summary (X out of Y passed).
        print(f"\n  Overall: {passed}/{len(self.last_results)} passed")
        # Line 62:  Print a closing separator.
        print(f"{'=' * 60}")
