# Line 1:  Import json for parsing and generating structured tool-call responses.
import json

# Line 2:  Import re for regex-based number extraction and operator detection from subtask text.
import re


# Line 3:  Define the SimulatedLM class that replaces a real LLM with keyword rules.
class SimulatedLM:
    # Line 4:  Initialize with an optional list of available tool names (discovered via MCP at runtime).
    def __init__(self, available_tools=None):
        # Line 5:  Store the available tools; if None, start with empty list (tools added later via MCP).
        self.available_tools = available_tools or []
        # Line 6:  Track how many times generate() has been called (useful for debugging and evals).
        self.call_count = 0

    # Line 7:  Update the set of available tools (called after MCP discovery completes).
    def update_tools(self, tool_names):
        # Line 8:  Replace the current tool list with newly discovered names from MCP servers.
        self.available_tools = list(tool_names)

    # Line 9:  Main generation method: given a subtask, tools, RAG context, and prior results, produce an action.
    def generate(self, subtask, rag_context="", prior_results=None):
        # Line 10:  Increment the call counter to track total LM invocations for this run.
        self.call_count += 1
        # Line 11:  Normalize the subtask text to lowercase for case-insensitive keyword matching.
        text = subtask.lower()
        # Line 12:  Default prior_results to empty list if not provided (first task has no context).
        prior_results = prior_results or []
        # Line 13:  Try to match a tool call pattern; pass prior results for value resolution.
        tool_call = self._try_tool_call(text, subtask, prior_results)
        # Line 14:  If a tool call was identified, return it immediately (no RAG needed for actions).
        if tool_call is not None:
            # Line 15:  Return the tool call as a dict with action="tool" and the tool/args payload.
            return {"action": "tool", **tool_call}
        # Line 16:  No tool matched — this is a knowledge question; use RAG context to answer.
        answer = self._answer_from_context(subtask, rag_context)
        # Line 17:  Return the answer as a dict with action="answer" and the generated text.
        return {"action": "answer", "text": answer}

    # Line 18:  Attempt to match the subtask against known tool patterns; returns None if no match.
    def _try_tool_call(self, text, original_text, prior_results):
        # Line 19:  --- ADDITION matching: look for "add", "+", or "calculate/compute" with a plus sign.
        wants_add = ("add" in text or "+" in text) and "add" in self.available_tools
        # Line 20:  If addition is wanted, extract two numbers from the text.
        if wants_add:
            # Line 21:  Find all integer values in the text using regex.
            nums = re.findall(r"\d+", text)
            # Line 22:  If we found at least two numbers, construct the add tool call.
            if len(nums) >= 2:
                # Line 23:  Return the structured tool call dict for the "add" tool.
                return {"tool": "add", "args": {"a": int(nums[0]), "b": int(nums[1])}}
        # Line 24:  --- SUBTRACTION matching: look for "subtract", "-", or "difference" with a minus sign.
        wants_subtract = (
            "subtract" in text or "difference" in text
        ) and "subtract" in self.available_tools
        # Line 25:  Guard: only match if we have the keyword (avoid false positives on hyphens in words).
        if wants_subtract:
            # Line 26:  Find all integer values in the text.
            nums = re.findall(r"\d+", text)
            # Line 27:  Require at least two numbers to avoid false positives.
            if len(nums) >= 2:
                # Line 28:  Return the structured tool call dict for the "subtract" tool.
                return {
                    "tool": "subtract",
                    "args": {"a": int(nums[0]), "b": int(nums[1])},
                }
        # Line 29:  --- MULTIPLICATION matching: look for "multiply", "*", or "product".
        wants_multiply = (
            "multiply" in text or "*" in text or "product" in text
        ) and "multiply" in self.available_tools
        # Line 30:  If multiplication is wanted, extract two numbers.
        if wants_multiply:
            # Line 31:  Find all integer values in the text.
            nums = re.findall(r"\d+", text)
            # Line 32:  If two numbers found, construct the multiply tool call.
            if len(nums) >= 2:
                # Line 33:  Return the structured tool call dict for the "multiply" tool.
                return {
                    "tool": "multiply",
                    "args": {"a": int(nums[0]), "b": int(nums[1])},
                }
        # Line 34:  --- MEMORY STORE matching: look for "store", "remember", "save".
        wants_store = (
            "store" in text or "remember" in text or "save" in text
        ) and "memory_store" in self.available_tools
        # Line 35:  If storing is wanted, extract key and value from the text and prior results.
        if wants_store:
            # Line 36:  Try to extract a key name (word after "as", "called", or "named").
            key_match = re.search(r"(?:as|called|named)\s+(\w+)", text)
            # Line 37:  Extract any explicit number in the subtask text as a potential value.
            val_match = re.findall(r"\d+", text)
            # Line 38:  Default key to "result" if no explicit key was found in the text.
            key = key_match.group(1) if key_match else "result"
            # Line 39:  Resolve the value: prefer explicit number > last prior result > fallback string.
            if val_match:
                # Line 40:  An explicit number exists in the subtask — use it directly.
                value = val_match[0]
            elif prior_results:
                # Line 41:  No explicit number, but we have prior task results — use the most recent one.
                #          This handles "store the result" where "the result" refers to previous output.
                value = str(prior_results[-1])
            else:
                # Line 42:  No number and no prior results — use a placeholder (toy limitation).
                value = "unknown"
            # Line 43:  Return the structured tool call for memory_store with resolved key and value.
            return {"tool": "memory_store", "args": {"key": key, "value": value}}
        # Line 44:  --- MEMORY RECALL matching: look for "recall", "what did i store".
        wants_recall = (
            "recall" in text or "what did i store" in text or "what is stored" in text
        ) and "memory_recall" in self.available_tools
        # Line 45:  If recalling is wanted, extract the target key.
        if wants_recall:
            # Line 46:  Try to extract the key to recall (word after "for" or "called").
            key_match = re.search(r"(?:for|called)\s+(\w+)", text)
            # Line 47:  Also try to find a standalone noun after "recall" (e.g., "recall total").
            if not key_match:
                # Line 48:  Try matching "recall <word>" pattern directly.
                key_match = re.search(r"recall\s+(\w+)", text)
            # Line 49:  Default key to "result" if no explicit key found.
            key = key_match.group(1) if key_match else "result"
            # Line 50:  Return the structured tool call for memory_recall with the target key.
            return {"tool": "memory_recall", "args": {"key": key}}
        # Line 51:  --- MEMORY LIST matching: look for "list" or "show all".
        wants_list = (
            "list" in text or "show all" in text
        ) and "memory_list" in self.available_tools
        # Line 52:  If listing is wanted, return the tool call (no arguments needed).
        if wants_list:
            # Line 53:  Return the structured tool call for memory_list.
            return {"tool": "memory_list", "args": {}}
        # Line 54:  No tool pattern matched; return None to signal "answer from context" path.
        return None

    # Line 55:  Generate a natural-language answer using the RAG-retrieved context.
    def _answer_from_context(self, subtask, rag_context):
        # Line 56:  If RAG context is available and non-empty, use it as the basis for the answer.
        if rag_context:
            # Line 57:  Extract meaningful keywords from the subtask (words longer than 3 chars).
            keywords = [w for w in subtask.lower().split() if len(w) > 3]
            # Line 58:  Best sentence found and its score (initialized to empty/zero).
            best_sentence = ""
            # Line 59:  Best score seen so far.
            best_score = -1
            # Line 60:  Source filename associated with the best sentence (for clean citation).
            best_source = "retrieved_document"
            # Line 61:  Split context into lines (each line is one document with [source: ...] prefix).
            lines = rag_context.split("\n")
            # Line 62:  Process each line to extract source and sentences separately.
            for line in lines:
                # Line 63:  Try to extract the source filename from the [source: xxx] prefix.
                source_match = re.match(r"\[source:\s*(\S+)\]\s*(.*)", line)
                # Line 64:  If we found a source marker, separate it from the text content.
                if source_match:
                    # Line 65:  Extract the filename (e.g., "doc1.txt").
                    src = source_match.group(1)
                    # Line 66:  Get the clean text without the source prefix.
                    clean_text = source_match.group(2)
                else:
                    # Line 67:  No source marker — use generic label and the whole line as text.
                    src = "retrieved_document"
                    # Line 68:  Use the full line as the text content.
                    clean_text = line
                # Line 69:  Split the clean text into sentences for granular matching.
                sentences = clean_text.split(". ")
                # Line 70:  Score each sentence by keyword overlap with the subtask.
                for sent in sentences:
                    # Line 71:  Count how many subtask keywords appear in this sentence.
                    score = sum(1 for kw in keywords if kw in sent.lower())
                    # Line 72:  If this sentence scores higher, update our best candidate.
                    if score > best_score:
                        # Line 73:  Update the best score.
                        best_score = score
                        # Line 74:  Store this clean sentence (no source prefix) as the answer body.
                        best_sentence = sent.strip()
                        # Line 75:  Remember which document this came from for citation.
                        best_source = src
            # Line 76:  If we found a relevant sentence with a positive score, return it cleanly.
            if best_sentence and best_score > 0:
                # Line 77:  Return the answer with a single clean citation at the end (no inline markers).
                return f"{best_sentence}. [source: {best_source}]"
        # Line 78:  No RAG context or no match found; return a generic "I don't know" fallback.
        return "I do not have enough information to answer that question."
