#!/bin/bash

# chmod +x screate_folders.sh

touch main.py
touch test_adversarial.py
touch README.md

mkdir -p harness/
touch harness/__init__.py
touch harness/trace_logger.py
touch harness/simulated_lm.py
touch harness/guardrails.py
touch harness/memory.py

mkdir -p mcp/
touch mcp/__init__.py
touch mcp/jsonrpc.py
touch mcp/server_math.py
touch mcp/server_memory.py
touch mcp/client.py

mkdir -p planner/
touch planner/__init__.py
touch planner/planner.py
touch planner/task_tracker.py

mkdir -p rag/
touch rag/__init__.py
touch rag/pipeline.py
mkdir -p rag/corpus/
touch rag/corpus/doc1.txt
touch rag/corpus/doc2.txt
touch rag/corpus/doc3.txt

mkdir -p sandbox/
touch sandbox/__init__.py
touch sandbox/executor.py

mkdir -p evaluator/
touch evaluator/__init__.py
touch evaluator/scorer.py

mkdir -p agent/
touch agent/__init__.py
touch agent/capstone_agent.py