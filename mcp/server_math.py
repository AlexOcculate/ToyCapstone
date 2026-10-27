# Line 1:  Import json for serializing tool definitions and results.
import json

# Line 2:  Import the jsonrpc helpers for building proper protocol messages.
from mcp.jsonrpc import make_response, parse_message


# Line 3:  Define the MathServer class that hosts math tools behind a JSON-RPC interface.
class MathServer:
    # Line 4:  Initialize the server with a name and an internal registry of tool functions.
    def __init__(self, name="math_server"):
        # Line 5:  Store the server name for identification in protocol messages.
        self.name = name
        # Line 6:  Register the tools this server provides (name → callable mapping).
        self._tools = {
            "add": self._tool_add,  # Line 7:  Add tool: returns sum of two numbers.
            "subtract": self._tool_subtract,  # Line 8:  Subtract tool: returns difference of two numbers.
            "multiply": self._tool_multiply,  # Line 9:  Multiply tool: returns product of two numbers.
        }
        # Line 10:  Track whether the server has been initialized via the protocol handshake.
        self.initialized = False

    # Line 11:  Handle incoming JSON-RPC messages (the main entry point for this server).
    def handle(self, raw_message):
        # Line 12:  Parse the raw message; if invalid, return a protocol error response.
        msg = parse_message(raw_message)
        # Line 13:  If parsing failed, return a JSON-RPC error indicating malformed request.
        if msg is None:
            # Line 14:  Return an error response with no valid request ID to correlate with.
            return make_response(
                "unknown", error={"code": -32700, "message": "Parse error"}
            )
        # Line 15:  Extract the method name from the parsed message to route to the right handler.
        method = msg.get("method", "")
        # Line 16:  Route to the appropriate handler based on the JSON-RPC method name.
        if method == "initialize":
            # Line 17:  Handle the initialization handshake (client announces itself).
            return self._handle_initialize(msg)
        elif method == "tools/list":
            # Line 18:  Handle tool discovery request (client asks what tools are available).
            return self._handle_tools_list(msg)
        elif method == "tools/call":
            # Line 19:  Handle a tool invocation request (client wants to execute a specific tool).
            return self._handle_tools_call(msg)
        else:
            # Line 20:  Unknown method — return a JSON-RPC "method not found" error.
            return make_response(
                msg.get("id"),
                error={"code": -32601, "message": f"Method not found: {method}"},
            )

    # Line 21:  Handle the initialize method: mark server as ready and confirm to client.
    def _handle_initialize(self, msg):
        # Line 22:  Mark this server as initialized (protocol handshake complete).
        self.initialized = True
        # Line 23:  Return a success response with server metadata (name and version).
        return make_response(
            msg["id"], result={"serverName": self.name, "version": "1.0"}
        )

    # Line 24:  Handle tools/list: return JSON schemas for all available tools on this server.
    def _handle_tools_list(self, msg):
        # Line 25:  Build a list of tool definition dicts (name, description, parameter schema).
        tools = []
        # Line 26:  Iterate over registered tools to build their JSON-RPC descriptions.
        for tool_name in self._tools:
            # Line 27:  Get the function's docstring as the tool description.
            desc = self._tools[tool_name].__doc__ or f"Execute {tool_name}"
            # Line 28:  Define parameter schema (simplified: just list expected param names).
            params_schema = self._get_param_schema(tool_name)
            # Line 29:  Append the tool definition to the response list.
            tools.append(
                {"name": tool_name, "description": desc, "inputSchema": params_schema}
            )
        # Line 30:  Return the list of tool definitions as the result.
        return make_response(msg["id"], result={"tools": tools})

    # Line 31:  Handle tools/call: execute the requested tool with provided arguments.
    def _handle_tools_call(self, msg):
        # Line 32:  Extract the tool name and arguments from the request params.
        params = msg.get("params", {})
        # Line 33:  Get the requested tool name from params.
        tool_name = params.get("name", "")
        # Line 34:  Get the arguments dict for the tool call.
        args = params.get("arguments", {})
        # Line 35:  Check if the requested tool exists in our registry.
        if tool_name not in self._tools:
            # Line 36:  Tool not found — return a JSON-RPC error with a clear message.
            return make_response(
                msg["id"],
                error={"code": -32602, "message": f"Unknown tool: {tool_name}"},
            )
        # Line 37:  Execute the tool function with the provided arguments (wrapped in try/except).
        try:
            # Line 38:  Call the actual tool function passing the arguments as keyword args.
            result = self._tools[tool_name](**args)
            # Line 39:  Return success response with the tool's return value.
            return make_response(
                msg["id"], result={"content": [{"type": "text", "text": str(result)}]}
            )
        # Line 40:  If the tool raised an exception, return a JSON-RPC error (don't crash the server).
        except Exception as e:
            # Line 41:  Return an error response containing the exception message.
            return make_response(
                msg["id"],
                error={"code": -32000, "message": f"Tool execution failed: {e}"},
            )

    # Line 42:  Get a simplified parameter schema for a given tool (for tools/list responses).
    def _get_param_schema(self, tool_name):
        # Line 43:  Define known parameter schemas for each math tool.
        schemas = {
            "add": {
                "type": "object",
                "properties": {"a": {"type": "number"}, "b": {"type": "number"}},
            },
            "subtract": {
                "type": "object",
                "properties": {"a": {"type": "number"}, "b": {"type": "number"}},
            },
            "multiply": {
                "type": "object",
                "properties": {"a": {"type": "number"}, "b": {"type": "number"}},
            },
        }
        # Line 44:  Return the schema for this tool, or an empty object if unknown.
        return schemas.get(tool_name, {})

    # ─── Actual Tool Implementations ────────────────────────────────────────

    # Line 45:  The add tool: returns the sum of two numbers a and b.
    def _tool_add(self, a, b):
        """Add two numbers together and return the sum."""
        # Line 46:  Return the arithmetic sum of the two input values.
        return a + b

    # Line 47:  The subtract tool: returns the difference (a minus b).
    def _tool_subtract(self, a, b):
        """Subtract b from a and return the difference."""
        # Line 48:  Return the arithmetic difference of the two input values.
        return a - b

    # Line 49:  The multiply tool: returns the product of two numbers.
    def _tool_multiply(self, a, b):
        """Multiply two numbers together and return the product."""
        # Line 50:  Return the arithmetic product of the two input values.
        return a * b
