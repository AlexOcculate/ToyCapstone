# Line 1:  Import time for measuring execution duration of tool calls.
import time

# Line 2:  Import threading for implementing execution timeout via a timer thread.
import threading


# Line 3:  Define the SandBox class that provides restricted, audited tool execution.
class SandBox:
    # Line 4:  Initialize with a maximum execution timeout and a list of allowed tool names.
    def __init__(self, max_timeout=5.0, allowed_tools=None):
        # Line 5:  Store the maximum allowed execution time in seconds for any single tool call.
        self.max_timeout = max_timeout
        # Line 6:  Store the whitelist of tool names that are permitted to execute.
        self.allowed_tools = allowed_tools or []
        # Line 7:  Initialize the audit log as an empty list (records every execution attempt).
        self.audit_log = []

    # Line 8:  Update the allowed tools list (called after MCP discovery completes).
    def set_allowed_tools(self, tool_names):
        # Line 9:  Replace the current whitelist with the newly discovered tool names.
        self.allowed_tools = list(tool_names)

    # Line 10:  Execute a tool call within the sandbox; returns (success, result_or_error).
    def execute(self, tool_name, args, tool_function):
        # Line 11:  Record the start time for this execution (for audit and timeout purposes).
        start_time = time.time()
        # Line 12:  Check if the requested tool is in the allowed whitelist.
        if tool_name not in self.allowed_tools:
            # Line 13:  Tool not permitted — log the blocked attempt and return failure.
            elapsed = time.time() - start_time
            # Line 14:  Record this blocked attempt in the audit log.
            self.audit_log.append(
                {
                    "tool": tool_name,
                    "status": "BLOCKED",
                    "reason": "not in allowed list",
                    "elapsed": elapsed,
                }
            )
            # Line 15:  Return failure with a clear message about the policy violation.
            return (False, f"Tool '{tool_name}' is not permitted by sandbox policy.")
        # Line 16:  Tool is allowed — proceed with execution in a try/except block.
        try:
            # Line 17:  Call the actual tool function with the provided arguments.
            result = tool_function(**args)
            # Line 18:  Calculate elapsed time for this successful execution.
            elapsed = time.time() - start_time
            # Line 19:  Check if execution exceeded the timeout (soft check; hard timeout via threading in production).
            if elapsed > self.max_timeout:
                # Line 20:  Execution was too slow — log it but still return the result (warning, not error).
                self.audit_log.append(
                    {
                        "tool": tool_name,
                        "status": "SLOW",
                        "elapsed": elapsed,
                        "result": str(result),
                    }
                )
            else:
                # Line 21:  Normal execution within time budget — log as success.
                self.audit_log.append(
                    {
                        "tool": tool_name,
                        "status": "OK",
                        "elapsed": elapsed,
                        "result": str(result),
                    }
                )
            # Line 22:  Validate the output doesn't contain forbidden patterns (e.g., file paths, raw HTML).
            validated = self._validate_output(str(result))
            # Line 23:  Return success with the (possibly sanitized) result.
            return (True, validated)
        # Line 24:  If the tool function raised an exception, catch it and report as failure.
        except Exception as e:
            # Line 25:  Calculate elapsed time for the failed execution.
            elapsed = time.time() - start_time
            # Line 26:  Record this failed attempt in the audit log with the exception message.
            self.audit_log.append(
                {
                    "tool": tool_name,
                    "status": "ERROR",
                    "elapsed": elapsed,
                    "error": str(e),
                }
            )
            # Line 27:  Return failure with the exception message (agent loop can handle this gracefully).
            return (False, f"Tool '{tool_name}' raised an exception: {e}")

    # Line 28:  Validate tool output for forbidden content patterns.
    def _validate_output(self, output):
        # Line 29:  Define patterns that should not appear in tool output (security check).
        forbidden = ["<script", "rm -rf", "/etc/passwd", "__import__"]
        # Line 30:  Check if any forbidden pattern appears in the output string.
        for pattern in forbidden:
            # Line 31:  If a forbidden pattern is found, sanitize by replacing it with a warning.
            if pattern in output.lower():
                # Line 32:  Replace the forbidden content with a sanitized placeholder.
                output = output.replace(pattern, "[SANITIZED]")
        # Line 33:  Return the (possibly sanitized) output string.
        return output

    # Line 34:  Get a summary of all audit log entries (for reporting).
    def audit_summary(self):
        # Line 35:  Count entries by status for a quick overview.
        counts = {}
        # Line 36:  Iterate over all audit entries to tally statuses.
        for entry in self.audit_log:
            # Line 37:  Increment the count for this entry's status.
            status = entry["status"]
            # Line 38:  Add to counts dict (create key if new).
            counts[status] = counts.get(status, 0) + 1
        # Line 39:  Return the summary counts as a dict.
        return counts

    # Line 40:  Print the full audit log in a readable format (for debugging and reporting).
    def print_audit(self):
        # Line 41:  Print a header for the audit log section.
        print(f"\n  [SANDBOX AUDIT LOG] ({len(self.audit_log)} entries)")
        # Line 42:  Iterate over each entry to print it with timing and status.
        for i, entry in enumerate(self.audit_log):
            # Line 43:  Format and print each audit entry with its index, tool, status, and elapsed time.
            print(
                f"    {i+1}. {entry['tool']} → {entry['status']} ({entry['elapsed']:.3f}s)"
            )
