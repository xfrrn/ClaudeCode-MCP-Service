# wechat_mcp/core/errors.py
ERROR_INVALID_INPUT = {
    "code": "invalid_input",
    "message": "Invalid input",
    "hint": "Check required fields and value types",
}
ERROR_NOT_IMPLEMENTED = {
    "code": "not_implemented",
    "message": "Not implemented",
    "hint": "Provide a real implementation in this tool",
}
ERROR_TOOL_NOT_FOUND = {
    "code": "tool_not_found",
    "message": "Tool not found",
    "hint": "Check tool name",
}
ERROR_TOOL_EXECUTION = {
    "code": "tool_error",
    "message": "Tool execution failed",
    "hint": "See error details",
}
ERROR_COOKIE_NOT_FOUND = {
    "code": "cookie_not_found",
    "message": "Cookie not found",
    "hint": "Check platform/account and cookie storage",
}
