# Line 1:  Define the Guardrails class that enforces safety boundaries on all inputs and iterations.
class Guardrails:
    # Line 2:  Initialize with configurable limits for input size, iteration count, and forbidden patterns.
    def __init__(
        self, max_input_length=500, max_iterations=10, forbidden_patterns=None
    ):
        # Line 3:  Store the maximum allowed input length (characters) to prevent oversized prompts.
        self.max_input_length = max_input_length
        # Line 4:  Store the maximum number of loop iterations to prevent infinite loops.
        self.max_iterations = max_iterations
        # Line 5:  Store forbidden patterns (regex strings) that must not appear in inputs.
        self.forbidden_patterns = forbidden_patterns or [
            r"__import__",
            r"os\.system",
            r"eval\(",
            r"exec\(",
        ]

    # Line 6:  Validate a user input string; returns (is_valid, reason) tuple.
    def validate_input(self, text):
        # Line 7:  If the input is empty or only whitespace, reject it immediately.
        if not text or not text.strip():
            # Line 8:  Return invalid with a clear reason for empty input.
            return (False, "Input is empty")
        # Line 9:  If the input exceeds the maximum length, reject it to prevent resource abuse.
        if len(text) > self.max_input_length:
            # Line 10:  Return invalid with a message indicating the size violation.
            return (
                False,
                f"Input exceeds max length ({len(text)} > {self.max_input_length})",
            )
        # Line 11:  Check each forbidden pattern against the input using regex search.
        for pattern in self.forbidden_patterns:
            # Line 12:  Import re here to avoid top-level import (keeps guardrails self-contained).
            import re as _re

            # Line 13:  If any forbidden pattern matches, reject the input with the pattern name.
            if _re.search(pattern, text):
                # Line 14:  Return invalid identifying which forbidden pattern was triggered.
                return (False, f"Forbidden pattern detected: {pattern}")
        # Line 15:  All checks passed; input is valid and safe to proceed with.
        return (True, "OK")

    # Line 16:  Check if the current iteration count has exceeded the maximum allowed.
    def check_iteration(self, current_count):
        # Line 17:  If current count exceeds max, return False (should stop) with a reason.
        if current_count > self.max_iterations:
            # Line 18:  Return False and a message indicating the iteration cap was hit.
            return (
                False,
                f"Max iterations exceeded ({current_count} > {self.max_iterations})",
            )
        # Line 19:  Within limits; return True to allow the next iteration to proceed.
        return (True, "OK")
