# Line 1:  Import time for timestamping log entries to show execution order.
import time

# Line 2:  Import collections for ordered grouping of log entries by component.
from collections import OrderedDict

# Line 3:  Define ANSI escape codes as module constants for reuse across the logger.
ANSI = {
    "reset": "\033[0m",  # Line 4:  Reset all formatting back to terminal default.
    "bold": "\033[1m",  # Line 5:  Bold text for headers and emphasis.
    "red": "\033[91m",  # Line 6:  Red foreground for guardrail/block messages.
    "green": "\033[92m",  # Line 7:  Green foreground for loop/progress messages.
    "yellow": "\033[93m",  # Line 8:  Yellow foreground for tool execution messages.
    "cyan": "\033[96m",  # Line 9:  Cyan foreground for LM and MCP wire messages.
    "magenta": "\033[95m",  # Line 10: Magenta foreground for planner decomposition messages.
    "white": "\033[97m",  # Line 11: White foreground for neutral informational text.
    "bg_green": "\033[42;30m",  # Line 12: Light green background + black fg for valid=True.
    "bg_red": "\033[41;97m",  # Line 13: Light red background + white fg for BLOCKED/invalid.
    "bg_yellow": "\033[43;30m",  # Line 14: Light yellow background + black fg for error/stopped.
}

# Line 15:  Map component names to their assigned ANSI color codes (capstone-specific palette).
COMPONENT_COLORS = {
    "loop": ANSI[
        "green"
    ],  # Line 16:  Agent loop messages in green (the heartbeat of execution).
    "lm": ANSI["cyan"],  # Line 17:  LM decisions in cyan (the "thinking" step).
    "tool": ANSI[
        "yellow"
    ],  # Line 18:  Tool execution in yellow (side effects / actions).
    "guardrail": ANSI["red"],  # Line 19:  Guardrail checks in red (safety boundary).
    "mcp": ANSI[
        "cyan"
    ],  # Line 20:  MCP protocol messages in cyan (wire-level, same as LM family).
    "planner": ANSI[
        "magenta"
    ],  # Line 21:  Planner decomposition in magenta (higher-level control).
    "rag": ANSI[
        "white"
    ],  # Line 22:  RAG retrieval in white (context grounding, neutral tone).
    "sandbox": ANSI[
        "yellow"
    ],  # Line 23:  SandBox execution in yellow (same family as tools, adds isolation).
    "evaluator": ANSI[
        "magenta"
    ],  # Line 24: Evaluator scoring in magenta (meta-observation layer).
    "memory": ANSI[
        "white"
    ],  # Line 25: Memory operations in white (passive storage, neutral).
}


# Line 26:  Define the TraceLogger class that accumulates colored log entries and renders a report.
class TraceLogger:
    # Line 27:  Initialize with an empty list of entries and a run label for identification.
    def __init__(self, run_label="capstone_run"):
        # Line 28:  Store the run label so the report header identifies which execution this is.
        self.run_label = run_label
        # Line 29:  Initialize the ordered list of log entries (each entry is a dict).
        self.entries = []
        # Line 30:  Record the start time for total elapsed calculation in the report.
        self.start_time = time.time()

    # Line 31:  Log a message with component tag, detail text, and optional status badge.
    def log(self, component, message, detail=None, status=None):
        # Line 32:  Get the color for this component from the palette (fallback to white).
        color = COMPONENT_COLORS.get(component, ANSI["white"])
        # Line 33:  Get current timestamp for ordering entries chronologically.
        ts = time.time()
        # Line 34:  Format the status badge with appropriate background color if provided.
        status_str = self._format_status(status) if status else ""
        # Line 35:  Build the colored line that will be printed and stored.
        line = f"{color}[{component:>9}] {message}{status_str}{ANSI['reset']}"
        # Line 36:  Store the entry as a dict for later report rendering with full metadata.
        self.entries.append(
            {
                "ts": ts,
                "component": component,
                "msg": message,
                "detail": detail,
                "status": status,
            }
        )
        # Line 37:  Print the line immediately so the user sees real-time progress in terminal.
        print(line)
        # Line 38:  If a detail string is provided, print it indented on the next line (uncolored for readability).
        if detail:
            # Line 39:  Indent detail text by 12 spaces to visually nest under the component line.
            print(f"{' ' * 12}{detail}")

    # Line 40:  Format a status string with background color based on its semantic meaning.
    def _format_status(self, status):
        # Line 41:  If status indicates success/valid, use green background (positive signal).
        if status in ("VALID", "OK", "DONE", "PASS"):
            # Line 42:  Return the formatted badge with light green bg and black foreground.
            return f" {ANSI['bg_green']}{status}{ANSI['reset']}"
        # Line 43:  If status indicates failure/block, use red background (negative signal).
        if status in ("BLOCKED", "FAIL", "INVALID", "ERROR"):
            # Line 44:  Return the formatted badge with light red bg and white foreground.
            return f" {ANSI['bg_red']}{status}{ANSI['reset']}"
        # Line 45:  For other statuses (STOPPED, TIMEOUT, etc.), use yellow background (caution).
        if status in ("STOPPED", "TIMEOUT", "INCOMPLETE"):
            # Line 46:  Return the formatted badge with light yellow bg and black foreground.
            return f" {ANSI['bg_yellow']}{status}{ANSI['reset']}"
        # Line 47:  Default: no background, just bold text for neutral statuses.
        return f" {ANSI['bold']}{status}{ANSI['reset']}"

    # Line 48:  Render the full report after execution completes; prints a structured summary.
    def report(self):
        # Line 49:  Calculate total elapsed time from start to now for the performance summary.
        elapsed = time.time() - self.start_time
        # Line 50:  Print a separator line to visually mark the beginning of the report section.
        print(f"\n{'=' * 60}")
        # Line 51:  Print the report header with run label and total entry count.
        print(
            f"{ANSI['bold']}  TRACE REPORT — {self.run_label} ({len(self.entries)} entries, {elapsed:.2f}s){ANSI['reset']}"
        )
        # Line 52:  Print another separator to close the header block.
        print(f"{'=' * 60}")
        # Line 53:  Iterate over all stored entries to print them in chronological order.
        for i, entry in enumerate(self.entries):
            # Line 54:  Get the color for this entry's component (same palette as live logging).
            color = COMPONENT_COLORS.get(entry["component"], ANSI["white"])
            # Line 55:  Format the elapsed offset from run start (shows relative timing).
            offset = entry["ts"] - self.start_time
            # Line 56:  Build the status badge for this entry using the same formatting logic.
            status_str = self._format_status(entry["status"]) if entry["status"] else ""
            # Line 57:  Print each entry with its timestamp offset, component, message, and status.
            print(
                f"  {color}[{offset:6.3f}s] [{entry['component']:>9}] {entry['msg']}{status_str}{ANSI['reset']}"
            )
            # Line 58:  If this entry has a detail string, print it indented under the main line.
            if entry["detail"]:
                # Line 59:  Indent detail by 14 spaces to align under the message text.
                print(f"  {' ' * 12}{entry['detail']}")
        # Line 60:  Print a final separator to close the report block.
        print(f"{'=' * 60}")
