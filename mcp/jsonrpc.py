# Line 1:  Import json for serializing and deserializing JSON-RPC messages.
import json

# Line 2:  Import uuid for generating unique request IDs required by the JSON-RPC spec.
import uuid


# Line 3:  Define a helper function to create a JSON-RPC request message.
def make_request(method, params=None):
    # Line 4:  Generate a unique ID for this request (JSON-RPC requires each request to have one).
    req_id = str(uuid.uuid4())[:8]
    # Line 5:  Build the request dict with jsonrpc version, method, params, and id fields.
    msg = {"jsonrpc": "2.0", "method": method, "params": params or {}, "id": req_id}
    # Line 6:  Serialize to JSON string (this is what would be sent over the wire in production).
    return json.dumps(msg)


# Line 7:  Define a helper function to create a JSON-RPC response message.
def make_response(req_id, result=None, error=None):
    # Line 8:  Build the base response dict with jsonrpc version and the original request id.
    msg = {"jsonrpc": "2.0", "id": req_id}
    # Line 9:  If there is an error, include it in the response (mutually exclusive with result).
    if error is not None:
        # Line 10:  Set the error field with the error message.
        msg["error"] = error
    # Line 11:  If there is a result and no error, include the result in the response.
    elif result is not None:
        # Line 12:  Set the result field with the successful response data.
        msg["result"] = result
    # Line 13:  Serialize to JSON string for transmission.
    return json.dumps(msg)


# Line 14:  Define a function to parse and validate an incoming JSON-RPC message.
def parse_message(raw):
    # Line 15:  Try to deserialize the raw string into a Python dict using json.loads.
    try:
        # Line 16:  Parse the JSON; if it fails, we'll catch the exception below.
        msg = json.loads(raw)
    # Line 17:  If JSON parsing fails (malformed input), return an error indicator.
    except (json.JSONDecodeError, TypeError):
        # Line 18:  Return None to signal that the message is not valid JSON-RPC.
        return None
    # Line 19:  Validate that the message has the required "jsonrpc" field set to "2.0".
    if msg.get("jsonrpc") != "2.0":
        # Line 20:  Missing or wrong version — treat as invalid message.
        return None
    # Line 21:  Return the parsed dict; caller will inspect method/params/result/error fields.
    return msg
