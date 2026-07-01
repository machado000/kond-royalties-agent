from mcp_server.mcp_stdio import handle_message


def test_initialize_returns_tools_capability() -> None:
    response = handle_message(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-06-18",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
        }
    )

    assert response is not None
    assert response["result"]["capabilities"]["tools"]["listChanged"] is False


def test_tools_list_returns_royalty_tools() -> None:
    response = handle_message({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})

    assert response is not None
    tool_names = [tool["name"] for tool in response["result"]["tools"]]
    assert "ask_royalties" in tool_names
    assert "run_royalty_query" in tool_names
    assert "describe_schema" in tool_names


def test_unknown_tool_returns_protocol_error() -> None:
    response = handle_message(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "unknown_tool", "arguments": {}},
        }
    )

    assert response is not None
    assert response["error"]["code"] == -32602
