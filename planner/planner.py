# Line 1:  Import re for regex-based sentence splitting in goal decomposition.
import re


# Line 2:  Define the Planner class that decomposes a complex goal into ordered subtasks.
class Planner:
    # Line 3:  Initialize with a maximum number of subtasks to prevent unbounded decomposition.
    def __init__(self, max_subtasks=5):
        # Line 4:  Store the maximum allowed subtask count (guardrail against over-decomposition).
        self.max_subtasks = max_subtasks

    # Line 5:  Decompose a goal string into a list of subtask description strings.
    def decompose(self, goal):
        # Line 6:  Normalize the goal by stripping whitespace and ensuring it's non-empty.
        goal = goal.strip()
        # Line 7:  If the goal is empty after stripping, return an empty list (no subtasks).
        if not goal:
            # Line 8:  Return empty list for empty goals.
            return []
        # Line 9:  Split the goal on common conjunctions and punctuation that indicate separate tasks.
        #         Patterns: "then", "and then", "after that", commas followed by action verbs.
        raw_parts = re.split(
            r"\b(?:then|and then|after that|, and|;)\b", goal, flags=re.IGNORECASE
        )
        # Line 10:  Also split on standalone commas if the parts are still too long (secondary split).
        refined_parts = []
        # Line 11:  Process each raw part to further split on commas if needed.
        for part in raw_parts:
            # Line 12:  Strip whitespace from the part.
            part = part.strip()
            # Line 13:  If the part contains a comma and is longer than 40 chars, split on comma.
            if "," in part and len(part) > 40:
                # Line 14:  Split on comma and extend the refined list with sub-parts.
                refined_parts.extend([p.strip() for p in part.split(",") if p.strip()])
            else:
                # Line 15:  Part is short enough or has no comma; add as-is.
                refined_parts.append(part)
        # Line 16:  Filter out any empty strings that may result from splitting.
        subtasks = [s for s in refined_parts if s]
        # Line 17:  Enforce the maximum subtask limit (truncate if exceeded).
        if len(subtasks) > self.max_subtasks:
            # Line 18:  Truncate to max and append a note about truncation.
            subtasks = subtasks[: self.max_subtasks]
        # Line 19:  Return the final list of subtask description strings.
        return subtasks
