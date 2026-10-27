# Line 1:  Import time for tracking execution duration across the full agent run.
import time

# Line 2:  Import the SimulatedLM from harness (the "brain" that decides actions).
from harness.simulated_lm import SimulatedLM

# Line 3:  Import Guardrails from harness (safety boundary enforcement on inputs and loops).
from harness.guardrails import Guardrails

# Line 4:  Import Memory from harness (agent's own working memory for cross-subtask context).
from harness.memory import Memory

# Line 5:  Import TraceLogger from harness (colored execution tracing for observability).
from harness.trace_logger import TraceLogger

# Line 6:  Import MCPClient from mcp (discovers and routes tool calls to external servers).
from mcp.client import MCPClient

# Line 7:  Import Planner from planner (decomposes complex goals into subtasks).
from planner.planner import Planner

# Line 8:  Import TaskTracker from planner (tracks state of each subtask through its lifecycle).
from planner.task_tracker import TaskTracker, TaskState

# Line 9:  Import RAGPipeline from rag (retrieves relevant documents to ground answers).
from rag.pipeline import RAGPipeline

# Line 10: Import SandBox from sandbox (restricted execution environment with audit logging).
from sandbox.executor import SandBox

# Line 11: Import Evaluator from evaluator (scores agent output against expected criteria).
from evaluator.scorer import Evaluator


# Line 12: Define the CapstoneAgent class that composes all previous modules into one system.
class CapstoneAgent:
    # Line 13: Initialize with all subsystem references; each is injected via constructor (dependency injection).
    def __init__(self, mcp_client, planner, rag_pipeline, sandbox, evaluator=None):
        # Line 14: Store the MCP client reference (manages connections to tool servers).
        self.mcp = mcp_client
        # Line 15: Store the Planner reference (decomposes goals into subtask lists).
        self.planner = planner
        # Line 16: Store the RAG pipeline reference (retrieves context documents per subtask).
        self.rag = rag_pipeline
        # Line 17: Store the SandBox reference (executes tools in a restricted environment).
        self.sandbox = sandbox
        # Line 18: Store the Evaluator reference (optional; used for self-scoring after runs).
        self.evaluator = evaluator
        # Line 19: Create a Guardrails instance with default safety limits.
        self.guardrails = Guardrails(max_input_length=500, max_iterations=10)
        # Line 20: Create the SimulatedLM and feed it the tools discovered via MCP.
        self.lm = SimulatedLM(available_tools=mcp_client.get_tool_names())
        # Line 21: Create an internal Memory instance for the agent's working context.
        self.memory = Memory()
        # Line 22: Create a TraceLogger for this agent instance (labeled "capstone").
        self.trace = TraceLogger(run_label="capstone_agent")
        # Line 23: Store the last run's final answer (for evaluator access and testing).
        self.last_answer = ""
        # Line 24: Store the list of tool calls made during the last run (for evaluator scoring).
        self.last_tool_calls = []

    # Line 25: Main execution method: takes a goal string, runs the full pipeline, returns final answer.
    def run(self, goal):
        # Line 26: Record the start time for this entire agent run (used by evaluator for latency).
        self._run_start = time.time()
        # Line 27: Reset per-run state: clear tool call log and previous answer.
        self.last_tool_calls = []
        # Line 28: Log the start of execution with the goal text.
        self.trace.log("loop", f"START: {goal[:80]}{'...' if len(goal) > 80 else ''}")
        # Line 29: Validate the input through guardrails before any processing begins.
        valid, reason = self.guardrails.validate_input(goal)
        # Line 30: If input is invalid, log the block and return an error message immediately.
        if not valid:
            # Line 31: Log the guardrail rejection with BLOCKED status.
            self.trace.log("guardrail", f"Input rejected: {reason}", status="BLOCKED")
            # Line 32: Return an error string as the agent's "answer" (graceful degradation).
            self.last_answer = f"[BLOCKED] {reason}"
            # Line 33: Return the blocked message to the caller.
            return self.last_answer
        # Line 34: Input is valid — log that guardrails passed.
        self.trace.log("guardrail", "Input validated", status="VALID")
        # Line 35: Use the Planner to decompose the goal into a list of subtask descriptions.
        subtasks = self.planner.decompose(goal)
        # Line 36: If decomposition produced zero subtasks, return a message indicating empty plan.
        if not subtasks:
            # Line 37: Log that the planner produced no subtasks (edge case).
            self.trace.log(
                "planner", "Decomposition produced 0 subtasks", status="INCOMPLETE"
            )
            # Line 38: Set the answer to indicate the plan was empty.
            self.last_answer = "No actionable subtasks were identified from this goal."
            # Line 39: Return early since there is nothing to execute.
            return self.last_answer
        # Line 40: Log the decomposition result showing how many subtasks were planned.
        self.trace.log(
            "planner",
            f"Decomposed into {len(subtasks)} subtask(s)",
            detail=" | ".join(subtasks),
        )
        # Line 41: Create a fresh TaskTracker for this run (tracks state of each subtask).
        tracker = TaskTracker()
        # Line 42: Register each subtask with the tracker in PENDING state.
        task_ids = []
        # Line 43: Iterate over subtasks to add them to the tracker and collect their IDs.
        for i, st in enumerate(subtasks):
            # Line 44: Add this subtask to the tracker; get back its assigned ID.
            tid = tracker.add_task(st)
            # Line 45: Append the task ID to our list for sequential access.
            task_ids.append(tid)
        # Line 46: Initialize a list to collect results from each subtask (for final answer compilation).
        results = []
        # Line 47: Track iteration count for the guardrail max-iterations check.
        iteration = 0
        # Line 48: Enter the main execution loop: process subtasks one at a time.
        while True:
            # Line 49: Increment the iteration counter (for guardrail enforcement).
            iteration += 1
            # Line 50: Check if we've exceeded the maximum allowed iterations.
            ok, reason = self.guardrails.check_iteration(iteration)
            # Line 51: If iteration cap hit, stop the loop and mark remaining tasks as incomplete.
            if not ok:
                # Line 52: Log that the iteration guardrail triggered a stop.
                self.trace.log("guardrail", f"Stopped: {reason}", status="STOPPED")
                # Line 53: Break out of the execution loop.
                break
            # Line 54: Get the next pending task from the tracker (FIFO order).
            current_task = tracker.get_next_pending()
            # Line 55: If no more pending tasks, all subtasks are done — exit the loop.
            if current_task is None:
                # Line 56: Log that all subtasks have been processed.
                self.trace.log("loop", "All subtasks completed")
                # Line 57: Break out of the execution loop (normal completion).
                break
            # Line 58: Mark this task as IN_PROGRESS in the tracker.
            tracker.start(current_task["id"])
            # Line 59: Log that we're starting work on this specific subtask.
            self.trace.log(
                "loop", f"Task {current_task['id']}: {current_task['description'][:60]}"
            )
            # Line 60: Retrieve relevant RAG context for this subtask (grounds the LM's decision).
            rag_context = self.rag.build_context(current_task["description"])
            # Line 61: Log if RAG found relevant context (helps debug retrieval quality).
            if rag_context:
                # Line 62: Log that RAG provided context, showing source filenames.
                sources = [
                    line.split("]")[0][9:]
                    for line in rag_context.split("\n")
                    if "[source:" in line
                ]
                # Line 63: Log the retrieval with source list as detail.
                self.trace.log("rag", f"Retrieved context from: {', '.join(sources)}")
            else:
                # Line 64: Log that RAG found no relevant documents for this subtask.
                self.trace.log("rag", "No relevant documents retrieved")
            # # Line 65: Ask the SimulatedLM to decide what action to take given the subtask and context.
            # decision = self.lm.generate(current_task["description"], rag_context)
            # # Line 66: Log the LM's decision (tool call or direct answer).
            # action_type = decision.get("action", "unknown")
            # # Line 67: Log what the LM decided to do.
            # self.trace.log("lm", f"Decision: {action_type}", detail=str(decision)[:100])
            # Line 65: Ask the SimulatedLM to decide what action to take, passing prior results for context.
            decision = self.lm.generate(
                current_task["description"], rag_context, prior_results=results
            )
            # Line 66: Log the LM's decision (tool call or direct answer).
            action_type = decision.get("action", "unknown")
            # Line 67: Log what the LM decided to do.
            self.trace.log("lm", f"Decision: {action_type}", detail=str(decision)[:100])

            # Line 68: Branch on the action type to execute the appropriate path.
            if action_type == "tool":
                # Line 69: The LM wants to call a tool — route through MCP → SandBox pipeline.
                result = self._execute_tool(
                    decision, current_task["id"], tracker, results
                )
            else:
                # Line 70: The LM wants to answer directly (knowledge question grounded in RAG).
                result = decision.get("text", "No answer generated.")
                # Line 71: Log the direct answer from the LM.
                self.trace.log(
                    "lm",
                    f"Direct answer: {result[:60]}{'...' if len(result) > 60 else ''}",
                )
                # Line 72: Mark this task as DONE with the direct answer as its result.
                tracker.complete(current_task["id"], result)
                # Line 73: Append the result to our results list for final compilation.
                results.append(result)
        # Line 74: After the loop ends, compile all subtask results into a final answer string.
        self.last_answer = self._compile_answer(results, tracker)
        # Line 75: Log the final compiled answer.
        self.trace.log(
            "loop",
            f"FINAL ANSWER: {self.last_answer[:80]}{'...' if len(self.last_answer) > 80 else ''}",
            status="DONE",
        )
        # Line 76: If an evaluator is attached, self-score this run automatically.
        if self.evaluator is not None:
            # Line 77: Log that self-evaluation is about to begin.
            self.trace.log("evaluator", "Running self-evaluation...")
        # Line 78: Return the final compiled answer to the caller.
        return self.last_answer

    # Line 79: Execute a tool call through the MCP → SandBox pipeline; handles errors gracefully.
    def _execute_tool(self, decision, task_id, tracker, results):
        # Line 80: Extract the tool name from the LM's decision dict.
        tool_name = decision.get("tool", "unknown")
        # Line 81: Extract the arguments dict for this tool call.
        args = decision.get("args", {})
        # Line 82: Log the tool call being attempted (name and arguments).
        self.trace.log("mcp", f"Calling tool: {tool_name}({args})")
        # Line 83: Record this tool call in our per-run log (for evaluator scoring later).
        self.last_tool_calls.append({"tool": tool_name, "args": args})
        # Line 84: Route the tool call through the MCP client (finds the right server).
        mcp_result = self.mcp.call_tool(tool_name, args)
        # Line 85: Check if the MCP call returned an error (server down, unknown tool, etc.).
        if "error" in mcp_result:
            # Line 86: Log the MCP-level error.
            self.trace.log(
                "mcp", f"Error from server: {mcp_result['error']}", status="ERROR"
            )
            # Line 87: Mark this task as FAILED with the MCP error message.
            tracker.fail(task_id, mcp_result["error"])
            # Line 88: Append an error note to results so the final answer reflects the failure.
            results.append(f"[Task {task_id} failed: {mcp_result['error']}]")
            # Line 89: Return the error message (agent loop continues to next subtask).
            return mcp_result["error"]
        # Line 90: MCP call succeeded — now execute the result through the SandBox for safety.
        #         In this toy, the "execution" is already done by the server; the sandbox
        #         validates the output and logs it to the audit trail.
        success, sandbox_result = self.sandbox.execute(
            tool_name=tool_name,  # Line 91: Pass the tool name for whitelist check.
            args=args,  # Line 92: Pass the arguments (for audit logging).
            tool_function=lambda **kw: mcp_result[
                "result"
            ],  # Line 93: The "function" just returns the MCP result.
        )
        # Line 94: Check if the sandbox execution was successful.
        if success:
            # Line 95: Log the successful tool execution with its result.
            self.trace.log(
                "sandbox", f"{tool_name} → {sandbox_result[:60]}", status="OK"
            )
            # Line 96: Mark this task as DONE with the tool's output as its result.
            tracker.complete(task_id, sandbox_result)
            # Line 97: Append the successful result to our results list.
            results.append(sandbox_result)
            # Line 98: Return the result string.
            return sandbox_result
        else:
            # Line 99: Sandbox execution failed — log the error.
            self.trace.log(
                "sandbox", f"{tool_name} failed: {sandbox_result[:60]}", status="ERROR"
            )
            # Line 100: Mark this task as FAILED with the sandbox error.
            tracker.fail(task_id, sandbox_result)
            # Line 101: Append a failure note to results.
            results.append(f"[Task {task_id} failed: {sandbox_result}]")
            # Line 102: Return the error message.
            return sandbox_result

    # Line 103: Compile all subtask results into a single coherent final answer string.
    def _compile_answer(self, results, tracker):
        # Line 104: If there are no results at all, return a default "no output" message.
        if not results:
            # Line 105: Return the empty-results indicator.
            return "No results were produced."
        # Line 106: Filter out error/failure notes to see if we have any successful results.
        successful = [r for r in results if not r.startswith("[Task")]
        # Line 107: If all tasks failed, compile an error summary instead of a normal answer.
        if not successful:
            # Line 108: Join all failure messages into a single error report string.
            return " | ".join(results)
        # Line 109: We have at least one successful result — join them with semicolons.
        compiled = "; ".join(successful)
        # Line 110: Check if any tasks failed (to append a warning about incomplete execution).
        failed_count = tracker.summary().get("failed", 0)
        # Line 111: If some tasks failed, append a note indicating partial completion.
        if failed_count > 0:
            # Line 112: Add a suffix noting that not all subtasks completed successfully.
            compiled += f" [Note: {failed_count} subtask(s) failed]"
        # Line 113: Return the final compiled answer string.
        return compiled

    # Line 114: Get the trace logger instance (exposed for external access in main.py and tests).
    def get_trace(self):
        # Line 115: Return the TraceLogger so callers can render the full report.
        return self.trace

    # Line 116: Get the sandbox audit summary (exposed for reporting in main.py).
    def get_audit_summary(self):
        # Line 117: Delegate to the sandbox's audit summary method.
        return self.sandbox.audit_summary()
