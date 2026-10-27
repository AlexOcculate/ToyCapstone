# Line 1:  Import json for parsing server responses.
import json

# Line 2:  Import the jsonrpc helpers for building request messages.
from mcp.jsonrpc import make_request, parse_message


# Line 3:  Define the MCPClient class that manages connections to multiple MCP servers.
class MCPClient:
    # Line 4:  Initialize with an empty list of connected servers and discovered tools.
    def __init__(self):
        # Line 5:  Store connected server instances (each is a class with a .handle() method).
        self.servers = []
        # Line 6:  Store all discovered tool names across all servers (flat list for LM reference).
        self.discovered_tools = []
        # Line 7:  Map each tool name to the server that provides it (for routing calls).
        self._tool_to_server = {}

    # Line 8:  Connect to a new MCP server: initialize, discover tools, register them.
    def connect(self, server):
        # Line 9:  Add the server instance to our list of connected servers.
        self.servers.append(server)
        # Line 10:  Send the initialize handshake to establish the protocol connection.
        init_req = make_request("initialize", {"clientName": "ToyCapstone"})
        # Line 11:  Send the request to the server and get its response.
        init_resp_raw = server.handle(init_req)
        # Line 12:  Parse the initialization response to verify success.
        init_resp = parse_message(init_resp_raw)
        # Line 13:  If initialization failed, log a warning but continue (resilient design).
        if init_resp is None or "error" in init_resp:
            # Line 14:  Print a warning that this server failed to initialize.
            print(f"  [MCP] WARNING: Server '{server.name}' failed to initialize.")
            # Line 15:  Remove the failed server from our list (don't route calls to it).
            self.servers.pop()
            # Line 16:  Return early since this server is not usable.
            return
        # Line 17:  Send tools/list request to discover what tools this server offers.
        list_req = make_request("tools/list", {})
        # Line 18:  Send the discovery request and get the response.
        list_resp_raw = server.handle(list_req)
        # Line 19:  Parse the tools/list response.
        list_resp = parse_message(list_resp_raw)
        # Line 20:  If the response is valid and contains a result with tools, register them.
        if list_resp and "result" in list_resp:
            # Line 21:  Get the list of tool definitions from the response.
            tools = list_resp["result"].get("tools", [])
            # Line 22:  Iterate over each discovered tool to register it.
            for tool_def in tools:
                # Line 23:  Add the tool name to our global discovered list.
                self.discovered_tools.append(tool_def["name"])
                # Line 24:  Map this tool name to the server that provides it (for routing).
                self._tool_to_server[tool_def["name"]] = server

    # Line 25:  Call a specific tool by name; routes to the correct server automatically.
    def call_tool(self, tool_name, arguments):
        # Line 26:  Check if the requested tool is in our registry of discovered tools.
        if tool_name not in self._tool_to_server:
            # Line 27:  Tool not found — return an error dict (not an exception, for agent loop safety).
            return {"error": f"Tool '{tool_name}' not found on any connected server."}
        # Line 28:  Get the server that hosts this tool.
        target_server = self._tool_to_server[tool_name]
        # Line 29:  Build a tools/call JSON-RPC request with the tool name and arguments.
        call_req = make_request(
            "tools/call", {"name": tool_name, "arguments": arguments}
        )
        # Line 30:  Send the call to the target server and get the raw response.
        resp_raw = target_server.handle(call_req)
        # Line 31:  Parse the response to extract the result or error.
        resp = parse_message(resp_raw)
        # Line 32:  If parsing failed, return a generic error (server may be down).
        if resp is None:
            # Line 33:  Return an error indicating the server response was unparseable.
            return {"error": "Server returned malformed response."}
        # Line 34:  If the response contains an error field, return it as an error dict.
        if "error" in resp:
            # Line 35:  Return the error message from the server.
            return {"error": resp["error"].get("message", "Unknown server error")}
        # Line 36:  Extract the text content from the successful result.
        content = resp.get("result", {}).get("content", [])
        # Line 37:  If content list is non-empty, return the first text item as the result.
        if content and content[0].get("type") == "text":
            # Line 38:  Return the tool's output text wrapped in a success dict.
            return {"result": content[0]["text"]}
        # Line 39:  Fallback: return empty result if content format is unexpected.
        return {"result": ""}

    # Line 40:  Get the list of all discovered tool names (for passing to SimulatedLM).
    def get_tool_names(self):
        # Line 41:  Return a copy of the discovered tools list (prevents external mutation).
        return list(self.discovered_tools)

    # Line 42:  Check if any servers are connected and initialized.
    def is_healthy(self):
        # Line 43:  Return True if at least one server is connected (basic health check).
        return len(self.servers) > 0
