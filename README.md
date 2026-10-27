# ToyCapstone (Module #10)

The final module of the TOYAGENTS curriculum. It composes MCP + Planner + RAG + SandBox + Evaluator into a single working agent system, proving that all previous concepts fit together without any new patterns.

Prerequisite: understand ToyEvaluator (module #9).

---

## What Is This?

Imagine you are the manager of a small office. You have a filing cabinet (RAG), a team of specialists on different floors (MCP servers), a task list you write each morning (Planner), a safety protocol for handling dangerous materials (SandBox), and a quality checklist you run at the end of each day (Evaluator). This module is that office in Python code. No new ideas are introduced — only wiring. If you understood modules #2, #4, #7, #8, and #9 individually, this module should feel like assembling furniture from an IKEA bag where every piece was already cut to size.

The key insight: **all previous concepts compose**. The agent loop is the same as module #0. The tools come from outside via a protocol (MCP). The goals are decomposed before execution (Planner). Answers are grounded in documents (RAG). Tools run in a restricted environment (SandBox). And after each run, the system grades itself (Evaluator). Nothing here is new — it is proof that the curriculum is complete.

---

## Folder Structure

```
ToyCapstone/
├── main.py                  # Entry point: wires everything and runs a demo scenario
├── test_adversarial.py      # 5 failure-mode tests proving the system survives chaos
├── README.md                # This file
├── harness/
│   ├── __init__.py
│   ├── trace_logger.py      # Colored execution tracing (ANSI, no external deps)
│   ├── simulated_lm.py      # Keyword-based "brain" that adapts to discovered tools
│   ├── guardrails.py        # Input validation + iteration cap + forbidden patterns
│   └── memory.py            # Simple key-value store for agent working context
├── mcp/
│   ├── __init__.py
│   ├── jsonrpc.py           # JSON-RPC message construction and parsing helpers
│   ├── server_math.py       # Server hosting add, subtract, multiply tools
│   ├── server_memory.py     # Server hosting memory_store, memory_recall, memory_list
│   └── client.py            # MCPClient: connects to servers, discovers, routes calls
├── planner/
│   ├── __init__.py
│   ├── planner.py           # Decomposes a goal string into ordered subtask list
│   └── task_tracker.py      # Tracks each subtask through PENDING → IN_PROGRESS → DONE/FAILED
├── rag/
│   ├── __init__.py
│   ├── pipeline.py          # TF-IDF embedding + cosine similarity retrieval + context build
│   └── corpus/
│       ├── doc1.txt         # About Paris / France (knowledge grounding demo)
│       ├── doc2.txt         # About Python programming
│       └── doc3.txt         # About speed of light / physics
├── sandbox/
│   ├── __init__.py
│   └── executor.py          # Restricted execution: whitelist, timeout, audit log, output validation
├── evaluator/
│   ├── __init__.py
│   └── scorer.py            # Test cases + scoring (keywords, tools, latency) + report
└── agent/
    ├── __init__.py
    └── capstone_agent.py    # The orchestrator: wires all subsystems into one run() method
```

---

## Dependencies

External: None. Pure Python standard library only.

Standard library modules used:

- json — serialize/deserialize JSON-RPC messages
- os — file path resolution for corpus loading
- re — regex for tokenization, keyword extraction, pattern matching
- math — cosine similarity (sqrt, log)
- time — timestamping in trace logger, latency measurement in evaluator
- threading — available for timeout enforcement (used conceptually in sandbox)
- collections — Counter for TF-IDF document frequency
- enum — TaskState constants in task tracker
- uuid — unique request IDs in JSON-RPC

Internal import graph (arrows mean "imports from"):

```
main.py  →  mcp, planner, rag, sandbox, evaluator, agent
agent/capstone_agent.py  →  harness, mcp, planner, rag, sandbox, evaluator
harness/simulated_lm.py  →  (stdlib only)
mcp/client.py  →  mcp/jsonrpc.py
mcp/server_math.py  →  mcp/jsonrpc.py
mcp/server_memory.py  →  mcp/jsonrpc.py
planner/planner.py  →  (stdlib only)
planner/task_tracker.py  →  (stdlib only)
rag/pipeline.py  →  (stdlib only)
sandbox/executor.py  →  (stdlib only)
evaluator/scorer.py  →  (stdlib only)
```

No circular imports. No cross-module imports from other TOYAGENTS modules.

---

## Execution

```bash
cd ToyCapstone/

# Run the main demo (full trace + results + evaluation)
python main.py

# Run the adversarial test suite (5 failure-mode proofs)
python test_adversarial.py
```

No installation steps. No virtual environment needed. Python 3.8 or later.

---

## Expected Output

Running `python main.py` produces colored terminal output showing:

1. Setup phase — each subsystem initializes and reports readiness
2. Demo run — the agent decomposes a 3-part goal, executes each part through MCP + SandBox, grounds the knowledge question with RAG
3. Results — final compiled answer + sandbox audit summary
4. Trace report — full chronological log of every decision, color-coded by component
5. Evaluation — the evaluator runs its test cases and prints pass/fail scores

Running `python test_adversarial.py` produces:

```
  TOYCAPSTONE — ADVERSARIAL TESTS
  --------------------------------------------------
  PASS  Broken LM / Chaotic output
  PASS  Hostile / Invalid input
  PASS  Tool execution failure
  PASS  Infinite loop / Max iterations
  PASS  Full chain failure (cascading)

  5/5 tests passed.
```

---

## Architecture Diagram

```
                        ┌─────────────────────────────────────────────┐
                        │              USER GOAL STRING               │
                        └──────────────────────┬──────────────────────┘
                                               │
                                               ▼
                        ┌─────────────────────────────────────────────┐
                        │            GUARDRAILS (validate)            │
                        │   input length, forbidden patterns,         │
                        │   max iterations                            │
                        └──────────────────────┬──────────────────────┘
                                               │ valid
                                               ▼
                        ┌─────────────────────────────────────────────┐
                        │              PLANNER (decompose)            │
                        │   "goal" → [subtask1, subtask2, ...]       │
                        └──────────────────────┬──────────────────────┘
                                               │ subtask list
                                               ▼
                        ┌─────────────────────────────────────────────┐
                        │          TASK TRACKER (state machine)       │
                        │   PENDING → IN_PROGRESS → DONE / FAILED    │
                        └──────────────────────┬──────────────────────┘
                                               │ next pending task
                                               ▼
              ┌──────────────────────────────────────────────────────────────┐
              │                    EXECUTION LOOP (per subtask)              │
              │                                                              │
              │  ┌──────────┐    ┌──────────────┐    ┌───────────────────┐  │
              │  │   RAG    │───▶│  SIMULATED   │───▶│  DECISION:        │  │
              │  │ retrieve │    │  LM (brain)  │    │  tool or answer?  │  │
              │  └──────────┘    └──────────────┘    └────────┬──────────┘  │
              │                                               │             │
              │                              ┌────────────────┴──────────┐  │
              │                              │                           │  │
              │                              ▼ tool call                 ▼ answer
              │                    ┌──────────────────┐      ┌────────────────────┐
              │                    │     MCP CLIENT   │      │  Use RAG context   │
              │                    │  (route to server)│     │  as final text     │
              │                    └────────┬─────────┘      └────────────────────┘
              │                             │                            │
              │                             ▼                            │
              │                    ┌──────────────────┐                  │
              │                    │    SANDBOX       │                  │
              │                    │ (whitelist,      │                  │
              │                    │  audit, timeout) │                  │
              │                    └────────┬─────────┘                  │
              │                             │                            │
              │                             ▼                            ▼
              │                    ┌──────────────────────────────────────────┐
              │                    │        RESULT → TaskTracker.complete()   │
              │                    └──────────────────────────────────────────┘
              └──────────────────────────────────────────────────────────────┘
                                               │
                                               │ all tasks done
                                               ▼
                        ┌─────────────────────────────────────────────┐
                        │         COMPILATION (join results)          │
                        └──────────────────────┬──────────────────────┘
                                               │
                                               ▼
                        ┌─────────────────────────────────────────────┐
                        │          EVALUATOR (self-score)             │
                        │   keywords + tools + latency → 0..1 score  │
                        └──────────────────────┬──────────────────────┘
                                               │
                                               ▼
                        ┌─────────────────────────────────────────────┐
                        │              FINAL ANSWER                   │
                        └─────────────────────────────────────────────┘


  MCP SERVERS (external tool providers):

  ┌────────────────────┐       ┌────────────────────┐
  │   MathServer       │       │   MemoryServer     │
  │                    │       │                    │
  │  • add(a, b)       │       │  • memory_store()  │
  │  • subtract(a, b)  │       │  • memory_recall() │
  │  • multiply(a, b)  │       │  • memory_list()   │
  └────────────────────┘       └────────────────────┘
         ▲                              ▲
         │    JSON-RPC over            │    JSON-RPC over
         │    in-memory call           │    in-memory call
         │                              │
  ┌──────┴──────────────────────────────┴──────┐
  │              MCP CLIENT                    │
  │  (discovers tools, routes calls by name)   │
  └────────────────────────────────────────────┘
```

Legend:

- Boxes with solid borders = components that hold state or logic
- Arrows = data flow direction
- The execution loop repeats for each subtask until all are DONE or FAILED
- MCP servers are "external" in the sense that they could be separate processes (in production, they would be)

---

## State Machine Diagram

The system has two nested state machines: an outer one (plan-level) and an inner one (per-subtask).

```
  OUTER LOOP (Plan-Level):

  ┌──────────┐     goal received      ┌──────────────┐
  │  IDLE    │───────────────────────▶│  PLANNING    │
  └──────────┘                        └──────┬───────┘
                                             │ subtasks created
                                             ▼
                                    ┌─────────────────┐
                          ┌────────▶│   EXECUTING     │◀────────┐
                          │         │ (loop over      │         │
                          │         │  subtasks)      │         │
                          │         └────────┬────────┘         │
                          │                  │ next pending     │
                          │                  ▼                  │
                          │         ┌─────────────────┐         │
                          │         │  ALL DONE?      │──No────┘
                          │         └────────┬────────┘
                          │                  │ Yes
                          │                  ▼
                          │         ┌─────────────────┐
                          │         │   COMPILING     │
                          │         └────────┬────────┘
                          │                  │
                          │                  ▼
                          │         ┌─────────────────┐
                          │         │   EVALUATING    │
                          │         └────────┬────────┘
                          │                  │
                          │                  ▼
                          │         ┌─────────────────┐
                          └─────────│     DONE        │
                                    └─────────────────┘

  Guards:
  • IDLE → PLANNING:       goal passes guardrails (valid input)
  • PLANNING → EXECUTING:  planner produced >= 1 subtask
  • EXECUTING → COMPILING: no more PENDING tasks OR iteration cap hit
  • Any state → BLOCKED:   guardrail rejects input (terminal, returns error)


  INNER LOOP (Per-Subtask):

  ┌──────────┐    tracker.start()    ┌───────────────┐
  │ PENDING  │──────────────────────▶│ IN_PROGRESS   │
  └──────────┘                       └───────┬───────┘
                                             │
                              LM decides action
                                             │
                        ┌────────────────────┴────────────────────┐
                        │                                         │
                        ▼ tool call                               ▼ answer
              ┌──────────────────┐                    ┌────────────────────┐
              │ MCP route +      │                    │ Use RAG context    │
              │ SandBox execute  │                    │ as result text     │
              └────────┬─────────┘                    └─────────┬──────────┘
                       │                                        │
                  success?                              (always succeeds)
                  ┌────┴────┐                                       │
                  │         │                                       │
                 Yes       No                                        │
                  │         │                                       │
                  ▼         ▼                                       ▼
         ┌────────────┐  ┌────────────┐                    ┌────────────┐
         │    DONE    │  │   FAILED   │                    │    DONE    │
         │ (result)   │  │ (error msg)│                    │ (answer)   │
         └────────────┘  └────────────┘                    └────────────┘

  Transitions:
  • PENDING → IN_PROGRESS:   tracker.start(task_id) called
  • IN_PROGRESS → DONE:      tool succeeded OR direct answer produced
  • IN_PROGRESS → FAILED:    MCP error OR SandBox rejection OR exception raised
```

State description table:

| State       | Meaning                            | Exit Condition                 |
| ----------- | ---------------------------------- | ------------------------------ |
| IDLE        | Agent waiting for a goal           | Goal received and validated    |
| PLANNING    | Decomposing goal into subtasks     | Subtask list produced          |
| EXECUTING   | Processing subtasks one by one     | All tasks terminal OR cap hit  |
| COMPILING   | Joining results into final string  | String assembled               |
| EVALUATING  | Scoring the run against test cases | Score computed                 |
| DONE        | Run complete, answer returned      | Terminal state                 |
| BLOCKED     | Input rejected by guardrails       | Terminal state (returns error) |
| PENDING     | Subtask waiting in queue           | Becomes IN_PROGRESS            |
| IN_PROGRESS | Subtask being executed             | Resolves to DONE or FAILED     |
| DONE        | Subtask completed with result      | Terminal (per task)            |
| FAILED      | Subtask errored out                | Terminal (per task)            |

---

## File Reference

**main.py** — The entry point. Wires all subsystems together (MCP servers, planner, RAG, sandbox, evaluator), assembles the CapstoneAgent, runs a demo goal that exercises every component, prints results, renders the trace report, and triggers self-evaluation. Think of it as the "power button" for the whole system.

**harness/trace_logger.py** — A colored logging utility using ANSI escape codes (no external packages). Each component gets its own color: loop=green, LM=cyan, tools=yellow, guardrails=red, planner=magenta, RAG=white, sandbox=yellow, evaluator=magenta. It accumulates entries during execution and renders a full chronological report at the end. The status badges (VALID, BLOCKED, ERROR, DONE) get background colors for instant visual scanning.

**harness/simulated_lm.py** — The "brain." Replaces a real LLM with keyword-matching rules. It looks at the subtask text, checks for operators (+, -, *), action words (store, recall, calculate), and matches them against the list of tools discovered via MCP at runtime. If no tool matches, it falls back to answering from RAG-retrieved context. The key design: `update_tools()` lets you swap the brain's knowledge of available actions without changing a single line of logic — this is the "swap the brain, keep the body" principle from module #0 applied to dynamic tool discovery.

**harness/guardrails.py** — The safety boundary. Validates input length, checks for forbidden patterns (like `__import__` or `os.system`), and enforces a maximum iteration count. It sits at two points in the flow: before any processing begins (input validation) and on every loop iteration (runaway prevention). Think of it as the security guard at the building entrance AND the fire alarm that triggers if you stay in one room too long.

**harness/memory.py** — A simple key-value store. In this module it is available but not heavily used by the agent itself (the MemoryServer handles persistent storage via MCP). It exists to show where an agent's own working memory would live if needed for cross-run persistence.

**mcp/jsonrpc.py** — Protocol helpers: functions to build JSON-RPC 2.0 request and response messages, and a parser that validates incoming messages. In production, these strings would travel over HTTP or stdio. Here they are passed directly as method arguments (in-memory), but the message format is identical to what you would see on the wire.

**mcp/server_math.py** — A tool server hosting three arithmetic tools (add, subtract, multiply). It speaks JSON-RPC: it handles `initialize`, `tools/list`, and `tools/call` methods. Each tool is a plain Python function wrapped in protocol handling. The server never knows who is calling it or what the agent is doing — it just answers protocol messages.

**mcp/server_memory.py** — A second tool server hosting three memory tools (store, recall, list). Same JSON-RPC interface as the math server. Having two servers demonstrates that MCP separates "who defines tools" from "who uses tools" — the agent code is identical whether there are 2 servers or 20.

**mcp/client.py** — The bridge between the agent and the servers. It connects to each server (initialize handshake + tools/list discovery), builds a flat registry of all available tool names, and routes `tools/call` requests to the correct server by name. If a server is down or returns malformed data, the client returns an error dict instead of raising — the agent loop handles it gracefully.

**planner/planner.py** — Takes a goal string and splits it into subtask descriptions using regex on conjunctions ("then", "and then", commas). Enforces a maximum subtask count. In production, this would be an LLM call ("break this goal into steps"). Here it is a simple split, but the interface is identical: `decompose(goal) -> [str]`.

**planner/task_tracker.py** — Manages the lifecycle of each subtask through states: PENDING, IN_PROGRESS, DONE, FAILED. Provides methods to start, complete, or fail a task, and to query the next pending task. The summary() method gives counts per state for reporting. This is the "clipboard" that keeps track of what you have done and what remains.

**rag/pipeline.py** — Implements retrieval-augmented generation using TF-IDF embeddings and cosine similarity. It loads .txt files from a corpus directory, builds a vocabulary, computes document vectors, and at query time finds the top-K most similar documents. The `build_context()` method formats retrieved documents with source labels for citation. No GPU, no model API — just math on word frequencies.

**rag/corpus/doc1.txt** — A short paragraph about Paris (capital of France). This is what makes the "what is the capital of France" question answerable by RAG retrieval.

**rag/corpus/doc2.txt** — A short paragraph about Python programming. Provides variety for the corpus and tests that irrelevant documents are scored lower.

**rag/corpus/doc3.txt** — A short paragraph about the speed of light. Third document for corpus diversity.

**sandbox/executor.py** — The restricted execution environment. Before any tool runs, the sandbox checks: (1) is this tool in the allowed whitelist? (2) does it complete within the time budget? (3) does its output contain forbidden patterns? Every attempt (success or failure) is recorded in an audit log. In production this would be a Docker container or WASM runtime; here it is a wrapper function with checks, but the concept is identical: restrict, limit, log.

**evaluator/scorer.py** — Automated testing of agent behavior. You define test cases (input + expected keywords + expected tools), run the agent on each, and score the output on three axes: keyword presence, tool-call correctness, and latency compliance. The composite score is a simple average. This is how you would catch regressions when swapping models or changing prompts in production.

**agent/capstone_agent.py** — The orchestrator. Its `run(goal)` method is the single entry point that drives the entire pipeline: validate → plan → loop (retrieve → think → act) → compile → evaluate. It holds references to all subsystems and coordinates their interaction. This file is where "wiring" happens — no new logic, just the sequence in which components are called.

**test_adversarial.py** — Five tests that prove the system survives failure conditions: a chaotic LM returning garbage, hostile/oversized/forbidden inputs, a server that always crashes, an infinite task queue, and a full cascade of simultaneous failures across MCP + sandbox + plan. All five must pass for the module to be considered complete.

---

## What This Teaches

| Concept                    | Where to Look                            | Key Insight                                                                                                                  |
| -------------------------- | ---------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| Tool discovery at runtime  | mcp/client.py — connect() method         | The agent does not hardcode its tools. Add a server, get new capabilities, zero code change.                                 |
| Goal decomposition         | planner/planner.py — decompose()         | A complex goal is just a list of simple goals executed in order. The "intelligence" is in the ordering.                      |
| State tracking             | planner/task_tracker.py — TaskState enum | Every subtask has a lifecycle. You can pause, resume, retry, or skip based on state.                                         |
| Grounded answers           | rag/pipeline.py — build_context()        | The agent does not "know" facts. It searches documents and pastes the relevant ones into its thinking.                       |
| Safe execution             | sandbox/executor.py — execute()          | Never trust tool output blindly. Check the whitelist, measure the time, validate the result, log everything.                 |
| Self-evaluation            | evaluator/scorer.py — run()              | An agent that cannot grade itself is an agent you cannot trust in production. Evals are your safety net.                     |
| Composition over invention | agent/capstone_agent.py — run()          | No new patterns here. Just calling existing components in the right order. If it feels boring, that is the point.            |
| Graceful degradation       | test_adversarial.py — all tests          | When one part fails, the system reports the failure and continues. It does not crash. It does not pretend everything worked. |

---

## Intuitive Summary (for non-IT readers)

Think of this module as a restaurant kitchen:

- The **Planner** is the head chef who reads the order ticket and breaks it into steps: "prep vegetables, cook protein, plate dessert."
- The **MCP servers** are the different stations in the kitchen (grill station, pastry station). Each station has its own tools (burner, oven, mixer). The head chef does not need to know how a burner works — just that it exists and what it does.
- The **RAG pipeline** is the recipe book on the shelf. When the chef needs to remember "how do we make our signature sauce?", they look it up in the book rather than relying on memory.
- The **SandBox** is the food safety inspector. Before anything goes to a customer, it checks: is this ingredient allowed? Did it cook for the right amount of time? Does it look safe? And it writes everything in the health inspection log.
- The **Evaluator** is the mystery diner who scores the meal at the end. Did the dish have the right flavors (keywords)? Was it prepared using the right method (tool calls)? Did it arrive in a reasonable time (latency)?

The **CapstoneAgent** is the head chef running the whole service. They do not cook, they do not bake, they do not inspect — they coordinate. And if the grill station breaks down (MCP failure), they note it on the ticket and move to the next step. The kitchen does not stop because one burner failed.

---

## Curriculum Context

This is the final module in the TOYAGENTS series. Each previous module taught one concept in isolation:

- Module #0 taught you the agent loop (harness)
- Module #2 taught you how tools are discovered externally (MCP)
- Module #4 taught you how to break big goals into small steps (Planner)
- Module #7 taught you how to ground answers in documents (RAG)
- Module #8 taught you how to execute tools safely (SandBox)
- Module #9 taught you how to test and score agent behavior (Evaluator)

Module #10 proves they all fit together. If you can read this file and say "I expected this" without being surprised, the curriculum has done its job.

---

Parent curriculum: https://github.com/AlexOcculate/TOYAGENTS
