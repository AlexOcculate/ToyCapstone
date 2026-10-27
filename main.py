# Line 1:  Import os for path resolution (ensures relative paths work from any CWD).
import os

# Line 2:  Change to the script's directory so relative imports and file paths resolve correctly.
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Line 3:  Print a banner identifying this as the ToyCapstone demo.
print("\n" + "=" * 60)
# Line 4:  Print the module title.
print("  TOYCAPSTONE — Module #10")
# Line 5:  Print a one-line description of what this demo shows.
print("  MCP + Planner + RAG + SandBox + Evaluator composed together")
# Line 6:  Print a closing banner line.
print("=" * 60)

# Line 7:  Import all subsystem components needed to build the agent.
from mcp.server_math import MathServer
from mcp.server_memory import MemoryServer
from mcp.client import MCPClient
from planner.planner import Planner
from rag.pipeline import RAGPipeline
from sandbox.executor import SandBox
from evaluator.scorer import Evaluator
from agent.capstone_agent import CapstoneAgent

# Line 8:  Print a section header for the setup phase.
print("\n[SETUP] Wiring subsystems...")

# Line 9:  Create the MCP client (manages connections to tool servers).
mcp = MCPClient()
# Line 10: Connect the math server (provides add, subtract, multiply tools).
mcp.connect(MathServer())
# Line 11: Print confirmation that math server is connected.
print(f"  Connected: MathServer ({len(mcp.discovered_tools)} tools so far)")
# Line 12: Connect the memory server (provides memory_store, memory_recall, memory_list).
mcp.connect(MemoryServer())
# Line 13: Print confirmation that memory server is connected.
print(f"  Connected: MemoryServer ({len(mcp.discovered_tools)} tools total)")

# Line 14: Create the Planner (decomposes goals into subtasks, max 5).
planner = Planner(max_subtasks=5)
# Line 15: Print confirmation that planner is ready.
print(f"  Planner ready (max_subtasks={planner.max_subtasks})")

# Line 16: Create the RAG pipeline pointing to our corpus of 3 documents.
rag = RAGPipeline(corpus_dir="rag/corpus", top_k=2)
# Line 17: Print confirmation showing how many documents were loaded.
print(f"  RAG pipeline loaded {len(rag.documents)} documents")

# Line 18: Create the SandBox with allowed tools from MCP discovery.
sandbox = SandBox(max_timeout=5.0, allowed_tools=mcp.get_tool_names())
# Line 19: Print confirmation that sandbox is configured.
print(
    f"  SandBox ready (allowed_tools={len(sandbox.allowed_tools)}, timeout={sandbox.max_timeout}s)"
)

# Line 20: Create the Evaluator with a latency budget of 10 seconds per run.
evaluator = Evaluator(latency_budget=10.0)
# Line 21: Add a test case: math operation should produce correct numeric answer.
evaluator.add_test_case(
    name="math_addition",
    input_text="Calculate 7 + 8",
    expected_keywords=["15"],
    expected_tools=["add"],
)
# Line 22: Add a test case: knowledge question should be grounded in RAG corpus.
evaluator.add_test_case(
    name="knowledge_france",
    input_text="What is the capital of France?",
    expected_keywords=["Paris"],
    expected_tools=[],
)
# Line 23: Print confirmation that evaluator has test cases loaded.
print(f"  Evaluator ready ({len(evaluator.test_cases)} test cases)")

# Line 24: Assemble the CapstoneAgent with all subsystems wired together.
agent = CapstoneAgent(
    mcp_client=mcp,  # Line 25: MCP client for tool discovery and routing.
    planner=planner,  # Line 26: Planner for goal decomposition.
    rag_pipeline=rag,  # Line 27: RAG for context retrieval.
    sandbox=sandbox,  # Line 28: SandBox for safe execution.
    evaluator=evaluator,  # Line 29: Evaluator for self-scoring.
)

# Line 30: Print a section header for the demo run.
print("\n[DEMO] Running capstone scenario...")
# Line 31: Define the complex goal that exercises all subsystems.
goal = "Calculate 10 + 5, store the result as total, then tell me what the capital of France is"
# Line 32: Print the goal so the user can see what's being executed.
print(f"  Goal: {goal}")
# Line 33: Print a separator before the trace output begins.
print()

# Line 34: Execute the agent on the demo goal (this produces all the colored trace output).
answer = agent.run(goal)

# Line 35: Print a section header for the results.
print("\n[RESULTS]")
# Line 36: Print the final compiled answer from the agent.
print(f"  Answer: {answer}")

# Line 37: Print the sandbox audit summary (shows which tools were executed and their status).
audit = agent.get_audit_summary()
# Line 38: Print the audit counts in a compact format.
print(f"  SandBox audit: {audit}")

# Line 39: Render the full trace report (all colored log entries in chronological order).
agent.get_trace().report()

# Line 40: Run the evaluator to score the agent's performance on its test cases.
print("\n[EVALUATION]")
# Line 41: Execute all evaluator test cases against the agent.
eval_results = evaluator.run(agent)
# Line 42: Print the formatted evaluation report.
evaluator.print_report()

# Line 43: Print a final closing message.
print("\n[DONE] ToyCapstone demo complete.")
