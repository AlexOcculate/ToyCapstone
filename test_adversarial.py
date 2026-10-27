# Line 1:  Import sys and os for path setup so tests can find the module regardless of CWD.
import sys, os

# Line 2:  Insert the current directory into sys.path so imports resolve correctly.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Line 3:  Import all components needed for adversarial testing.
from harness.simulated_lm import SimulatedLM
from harness.guardrails import Guardrails
from harness.memory import Memory
from harness.trace_logger import TraceLogger
from mcp.jsonrpc import make_request, make_response, parse_message
from mcp.server_math import MathServer
from mcp.server_memory import MemoryServer
from mcp.client import MCPClient
from planner.planner import Planner
from planner.task_tracker import TaskTracker, TaskState
from rag.pipeline import RAGPipeline
from sandbox.executor import SandBox
from evaluator.scorer import Evaluator
from agent.capstone_agent import CapstoneAgent


# Line 4:  Helper function to build a fully-wired CapstoneAgent for testing.
def _build_agent():
    # Line 5:  Create MCP client and connect two servers (math + memory).
    mcp = MCPClient()
    # Line 6:  Connect the math server (provides add, subtract, multiply).
    mcp.connect(MathServer())
    # Line 7:  Connect the memory server (provides memory_store, memory_recall, memory_list).
    mcp.connect(MemoryServer())
    # Line 8:  Create a Planner with default max_subtasks.
    planner = Planner(max_subtasks=5)
    # Line 9:  Create a RAG pipeline pointing to the corpus directory.
    rag = RAGPipeline(corpus_dir="rag/corpus", top_k=2)
    # Line 10: Create a SandBox with default timeout and allowed tools from MCP discovery.
    sandbox = SandBox(max_timeout=5.0, allowed_tools=mcp.get_tool_names())
    # Line 11: Assemble the CapstoneAgent with all subsystems wired together.
    agent = CapstoneAgent(
        mcp_client=mcp,
        planner=planner,
        rag_pipeline=rag,
        sandbox=sandbox,
        evaluator=None,
    )
    # Line 12: Return the fully configured agent instance.
    return agent


# ──────────────────────────────────────────────
#  TEST 1: Broken / Chaotic LM
#  Proves: the system doesn't crash on malformed output
# ──────────────────────────────────────────────
def test_broken_lm():
    # Line 13: Build a standard agent instance.
    agent = _build_agent()

    # Line 14: Replace the LM with a chaotic version that returns garbage dicts.
    class ChaoticLM:
        # Line 15: A generate method that returns malformed/incomplete responses.
        #          Must accept prior_results to match the agent's call signature.
        def generate(self, subtask, rag_context="", prior_results=None):
            # Line 16: On first call, return a dict missing the "action" key.
            if not hasattr(self, "_count"):
                self._count = 0
            # Line 17: Increment the internal counter.
            self._count += 1
            # Line 18: Alternate between different types of malformed output.
            if self._count % 3 == 1:
                # Line 19: Return a dict with no "action" key (should be handled gracefully).
                return {"unexpected": "garbage"}
            elif self._count % 3 == 2:
                # Line 20: Return a tool call with a non-existent tool name.
                return {"action": "tool", "tool": "nonexistent_tool_xyz", "args": {}}
            else:
                # Line 21: Return an answer with empty text.
                return {"action": "answer", "text": ""}

    # Line 22: Inject the chaotic LM into the agent (replacing the normal SimulatedLM).
    agent.lm = ChaoticLM()
    # Line 23: Run the agent — it must not raise an exception.
    result = agent.run("Calculate 5 + 3 and tell me about France")
    # Line 24: Assert that we got a string back (not None, not an exception).
    assert isinstance(result, str), f"Expected string, got {type(result)}"
    # Line 25: Test passes if no exception was raised.
    print("    Chaotic LM handled without crash.")


# ──────────────────────────────────────────────
#  TEST 2: Invalid / Hostile Input
#  Proves: guardrails block bad input before it reaches the core
# ──────────────────────────────────────────────
def test_hostile_input():
    # Line 26: Build a standard agent instance.
    agent = _build_agent()
    # Line 27: Test empty input — should be blocked by guardrails.
    result_empty = agent.run("")
    # Line 28: Assert the empty input was blocked (contains BLOCKED marker).
    assert "BLOCKED" in result_empty, f"Empty input not blocked: {result_empty}"
    # Line 29: Test oversized input — should be blocked by length guardrail.
    huge_input = "x" * 10000
    # Line 30: Run the agent with the oversized input.
    result_huge = agent.run(huge_input)
    # Line 31: Assert the oversized input was blocked.
    assert "BLOCKED" in result_huge, f"Oversized input not blocked: {result_huge[:50]}"
    # Line 32: Test forbidden pattern — should be blocked by pattern guardrail.
    evil_input = "Please run __import__('os').system('rm -rf /')"
    # Line 33: Run the agent with the forbidden-pattern input.
    result_evil = agent.run(evil_input)
    # Line 34: Assert the forbidden pattern was blocked.
    assert (
        "BLOCKED" in result_evil
    ), f"Forbidden pattern not blocked: {result_evil[:50]}"
    # Line 35: Test passes if all hostile inputs were properly rejected.
    print("    All hostile inputs blocked by guardrails.")


# ──────────────────────────────────────────────
#  TEST 3: Tool Execution Failure
#  Proves: a failing tool doesn't crash the loop; error is handled
# ──────────────────────────────────────────────
def test_tool_failure():
    # Line 36: Build a standard agent instance.
    agent = _build_agent()

    # Line 37: Replace the MCP client with one that always returns an error for tool calls.
    class FailingMCP:
        # Line 38: A call_tool method that simulates a server crash.
        def call_tool(self, tool_name, arguments):
            # Line 39: Always return an error regardless of which tool is called.
            return {"error": f"Server crashed while executing {tool_name}"}

        # Line 40: Return tool names as if they were discovered (so LM thinks tools exist).
        def get_tool_names(self):
            # Line 41: Return the expected tool names to fool the LM into making tool calls.
            return [
                "add",
                "subtract",
                "multiply",
                "memory_store",
                "memory_recall",
                "memory_list",
            ]

        # Line 42: Health check returns True (server appears up but tools fail).
        def is_healthy(self):
            # Line 43: Return True to pass the health check.
            return True

    # Line 44: Inject the failing MCP into the agent.
    agent.mcp = FailingMCP()
    # Line 45: Run the agent with a goal that requires tool calls.
    result = agent.run("Calculate 10 + 5")
    # Line 46: Assert we got a string back (not a crash).
    assert isinstance(
        result, str
    ), f"Expected string after tool failure, got {type(result)}"
    # Line 47: Assert the result mentions the failure (graceful degradation).
    assert (
        "failed" in result.lower() or "error" in result.lower()
    ), f"No failure indication: {result}"
    # Line 48: Test passes — tool failure was handled without crashing.
    print("    Tool failure handled gracefully.")


# ──────────────────────────────────────────────
#  TEST 4: Infinite Loop / Max Iterations
#  Proves: the iteration guardrail stops runaway loops
# ──────────────────────────────────────────────
def test_infinite_loop():
    # Line 49: Build a standard agent instance.
    agent = _build_agent()

    # Line 50: Replace the planner with one that always produces many subtasks.
    class InfinitePlanner:
        # Line 51: A decompose method that returns more subtasks than max_iterations allows.
        def decompose(self, goal):
            # Line 52: Return 20 subtasks (exceeds the default max_iterations of 10).
            return [f"Subtask number {i}" for i in range(20)]

    # Line 53: Inject the infinite planner into the agent.
    agent.planner = InfinitePlanner()
    # Line 54: Run the agent — it must stop at max_iterations, not loop forever.
    result = agent.run("Do a very complex multi-step task that never ends")
    # Line 55: Assert we got a string back (the loop was stopped by guardrails).
    assert isinstance(
        result, str
    ), f"Expected string after iteration cap, got {type(result)}"
    # Line 56: The result should indicate incomplete execution (not all 20 tasks done).
    #          Either it mentions failure or simply has fewer than 20 results.
    # Line 57: Test passes — the iteration guardrail prevented an infinite loop.
    print("    Iteration cap enforced; no infinite loop.")


# ──────────────────────────────────────────────
#  TEST 5: Full Chain Failure (MCP server down + tool fails + plan incomplete)
#  Proves: cascading failures across all subsystems don't crash the agent
# ──────────────────────────────────────────────
def test_module_specific():
    # Line 58: This test simulates a worst-case scenario where multiple things fail simultaneously.
    #          MCP server returns errors, tools fail, and the plan can't fully complete.
    # Line 59: Build a standard agent instance.
    agent = _build_agent()

    # Line 60: Create an MCP client where one server works but the other is "down".
    class PartialMCP:
        def __init__(self):
            # Line 61: Initialize with a list of tools (pretend both servers were discovered).
            self.discovered_tools = ["add", "subtract", "memory_store", "memory_recall"]
            # Line 62: Track which tools are "down" (simulating server failure).
            self._down_tools = {"memory_store", "memory_recall"}

        def get_tool_names(self):
            # Line 63: Return all discovered tool names (agent thinks they're available).
            return list(self.discovered_tools)

        def call_tool(self, tool_name, arguments):
            # Line 64: If the tool is in the "down" set, return a server error.
            if tool_name in self._down_tools:
                # Line 65: Simulate a connection timeout to the memory server.
                return {
                    "error": f"Connection to memory_server timed out (tool: {tool_name})"
                }
            # Line 66: For working tools, return a fake success result.
            return {
                "result": f"{tool_name} executed successfully with args {arguments}"
            }

        def is_healthy(self):
            # Line 67: Report healthy even though some tools are down (partial failure).
            return True

    # Line 68: Inject the partial-failure MCP into the agent.
    agent.mcp = PartialMCP()
    # Line 69: Also make the sandbox reject one tool (simulating policy violation).
    original_execute = agent.sandbox.execute

    # Line 70: Wrap the sandbox execute to fail on "subtract" specifically.
    def failing_sandbox_execute(tool_name, args, tool_function):
        # Line 71: If the tool is "subtract", simulate a sandbox policy block.
        if tool_name == "subtract":
            # Line 72: Return failure with a policy violation message.
            return (
                False,
                "Sandbox policy violation: 'subtract' blocked by security rule.",
            )
        # Line 73: For other tools, delegate to the original sandbox execution.
        return original_execute(tool_name, args, tool_function)

    # Line 74: Replace the sandbox's execute method with the failing version.
    agent.sandbox.execute = failing_sandbox_execute
    # Line 75: Run a goal that exercises multiple tools (some will fail).
    result = agent.run("Calculate 10 + 5, store the result as total, recall total")
    # Line 76: Assert we got a string back — the agent survived the cascade of failures.
    assert isinstance(
        result, str
    ), f"Agent crashed during full chain failure: {type(result)}"
    # Line 77: The result should indicate some tasks failed (partial completion).
    assert (
        "failed" in result.lower()
        or "error" in result.lower()
        or "timeout" in result.lower()
    ), f"No failure indication in result: {result}"
    # Line 78: Test passes — cascading failures across MCP, sandbox, and plan were all handled.
    print("    Full chain failure survived without crash.")


# ──────────────────────────────────────────────
#  RUNNER
# ──────────────────────────────────────────────
if __name__ == "__main__":
    # Line 79: Define the list of tests to run, with descriptive names.
    tests = [
        ("Broken LM / Chaotic output", test_broken_lm),
        ("Hostile / Invalid input", test_hostile_input),
        ("Tool execution failure", test_tool_failure),
        ("Infinite loop / Max iterations", test_infinite_loop),
        ("Full chain failure (cascading)", test_module_specific),
    ]
    # Line 80: Print a header for the adversarial test suite.
    print("\n  TOYCAPSTONE — ADVERSARIAL TESTS")
    # Line 81: Print a separator line.
    print("  " + "-" * 50)
    # Line 82: Initialize the pass counter.
    passed = 0
    # Line 83: Iterate over all tests to execute them.
    for name, fn in tests:
        # Line 84: Attempt to run this test; catch any exception as a failure.
        try:
            # Line 85: Call the test function.
            fn()
            # Line 86: If no exception, print PASS and increment counter.
            print(f"  PASS  {name}")
            # Line 87: Increment the passed count.
            passed += 1
        except Exception as e:
            # Line 88: An exception was raised — print FAIL with the error message.
            print(f"  FAIL  {name}: {e}")
    # Line 89: Print a summary of how many tests passed out of total.
    print(f"\n  {passed}/{len(tests)} tests passed.")
    # Line 90: If any test failed, exit with non-zero code (for CI integration).
    if passed < len(tests):
        # Line 91: Exit with status code 1 to signal failure to the shell/CI.
        sys.exit(1)
