# Line 1:  Import json for serializing tool definitions and results.
import json

# Line 2:  Import the jsonrpc helpers for building proper protocol messages.
from mcp.jsonrpc import make_response, parse_message


# Line 3:  Define the MemoryServer class that hosts memory tools behind a JSON-RPC interface.
class MemoryServer:
    # Line 4:  Initialize the server with a name and an internal key-value store.
    def __init__(self, name="memory_server"):
        # Line 5:  Store the server name for identification in protocol messages.
        self.name = name
        # Line 6:  The actual storage backend is a simple dict (in production this could be a DB).
        self._store = {}
        # Line 7:  Register the tools this server provides.
        self._tools = {
            "memory_store": self._tool_store,  # Line 8:  Store a value under a key.
            "memory_recall": self._tool_recall,  # Line 9:  Retrieve a value by key.
            "memory_list": self._tool_list,  # Line 10: List all stored keys.
        }
        # Line 11:  Track whether the server has been initialized via the protocol handshake.
        self.initialized = False

    # Line 12:  Handle incoming JSON-RPC messages (same interface as MathServer).
    def handle(self, raw_message):
        # Line 13:  Parse the raw message; if invalid, return a protocol error response.
        msg = parse_message(raw_message)
        # Line 14:  If parsing failed, return an error for malformed input.
        if msg is None:
            # Line 15:  Return a parse error response.
            return make_response(
                "unknown", error={"code": -32700, "message": "Parse error"}
            )
        # Line 16:  Route based on the JSON-RPC method name.
        method = msg.get("method", "")
        # Line 17:  Handle initialization handshake.
        if method == "initialize":
            # Line 18:  Mark as initialized and confirm.
            self.initialized = True
            # Line 19:  Return server metadata in the response.
            return make_response(
                msg["id"], result={"serverName": self.name, "version": "1.0"}
            )
        elif method == "tools/list":
            # Line 20:  Return available tool definitions for this memory server.
            tools = []
            # Line 21:  Build tool descriptions from registered functions.
            for tool_name in self._tools:
                # Line 22:  Get docstring as description.
                desc = self._tools[tool_name].__doc__ or f"Execute {tool_name}"
                # Line 23:  Get parameter schema for this tool.
                params_schema = self._get_param_schema(tool_name)
                # Line 24:  Append to the tools list.
                tools.append(
                    {
                        "name": tool_name,
                        "description": desc,
                        "inputSchema": params_schema,
                    }
                )
            # Line 25:  Return the tool list as result.
            return make_response(msg["id"], result={"tools": tools})
        elif method == "tools/call":
            # Line 26:  Execute the requested memory tool.
            params = msg.get("params", {})
            # Line 27:  Extract tool name and arguments.
            tool_name = params.get("name", "")
            # Line 28:  Get the arguments for this call.
            args = params.get("arguments", {})
            # Line 29:  Validate that the tool exists.
            if tool_name not in self._tools:
                # Line 30:  Return error for unknown tool.
                return make_response(
                    msg["id"],
                    error={"code": -32602, "message": f"Unknown tool: {tool_name}"},
                )
            # Line 31:  Execute the tool in a try/except to prevent server crashes.
            try:
                # Line 32:  Call the tool function with provided arguments.
                result = self._tools[tool_name](**args)
                # Line 33:  Return success with the result text.
                return make_response(
                    msg["id"],
                    result={"content": [{"type": "text", "text": str(result)}]},
                )
            except Exception as e:
                # Line 34:  Return error if tool execution failed.
                return make_response(
                    msg["id"], error={"code": -32000, "message": f"Tool failed: {e}"}
                )
        else:
            # Line 35:  Unknown method — return method-not-found error.
            return make_response(
                msg.get("id"),
                error={"code": -32601, "message": f"Method not found: {method}"},
            )

    # Line 36:  Get parameter schema for memory tools.
    def _get_param_schema(self, tool_name):
        # Line 37:  Define schemas for each memory tool's expected parameters.
        schemas = {
            "memory_store": {
                "type": "object",
                "properties": {"key": {"type": "string"}, "value": {"type": "string"}},
            },
            "memory_recall": {
                "type": "object",
                "properties": {"key": {"type": "string"}},
            },
            "memory_list": {"type": "object", "properties": {}},
        }
        # Line 38:  Return the matching schema or empty object.
        return schemas.get(tool_name, {})

    # ─── Actual Tool Implementations ────────────────────────────────────────

    # Line 39:  The memory_store tool: persists a value under a given key.
    def _tool_store(self, key, value):
        """Store a value in memory under the specified key."""
        # Line 40:  Write the value to the internal store dict.
        self._store[str(key)] = str(value)
        # Line 41:  Return a confirmation message (the tool's "output" for the agent).
        return f"Stored '{key}' = '{value}'"

    # Line 42:  The memory_recall tool: retrieves a previously stored value by key.
    def _tool_recall(self, key):
        """Recall a previously stored value from memory by its key."""
        # Line 43:  Look up the key in the store; return "not found" message if absent.
        if str(key) not in self._store:
            # Line 44:  Key doesn't exist — return an informative "not found" string.
            return f"Key '{key}' not found in memory."
        # Line 45:  Key exists — return the stored value.
        return f"{key} = {self._store[str(key)]}"

    # Line 46:  The memory_list tool: lists all currently stored keys and values.
    def _tool_list(self):
        """List all keys currently stored in memory."""
        # Line 47:  If the store is empty, return a message indicating no items.
        if not self._store:
            # Line 48:  Return the empty-store indicator.
            return "Memory is empty."
        # Line 49:  Format all key-value pairs as a readable string.
        items = ", ".join(f"{k}={v}" for k, v in sorted(self._store.items()))
        # Line 50:  Return the formatted list of all stored items.
        return f"Stored items: {items}"
