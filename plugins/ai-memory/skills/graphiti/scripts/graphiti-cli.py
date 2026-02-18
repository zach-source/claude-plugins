#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx"]
# ///
"""Graphiti CLI - Interact with the Graphiti knowledge graph via HTTP.

Usage:
  uv run graphiti-cli.py status
  uv run graphiti-cli.py add "Fix: build error" "Problem: X. Solution: Y." [--source text] [--desc "bug fix"]
  uv run graphiti-cli.py search "kubernetes deployment"
  uv run graphiti-cli.py facts "nix build errors"
  uv run graphiti-cli.py episodes [--limit 10] [--group claude_memory]
  uv run graphiti-cli.py delete-episode <episode-id>
  uv run graphiti-cli.py tools
"""
import argparse
import json
import sys
import textwrap

import httpx

DEFAULT_URL = "http://127.0.0.1:51847/mcp/"
DEFAULT_GROUP = "claude_memory"
PROTOCOL_VERSION = "2025-03-26"


def jsonrpc(method: str, params: dict | None = None, req_id: int = 1) -> dict:
    payload = {"jsonrpc": "2.0", "id": req_id, "method": method}
    if params is not None:
        payload["params"] = params
    return payload


class GraphitiClient:
    def __init__(self, url: str = DEFAULT_URL, timeout: float = 30.0):
        self.url = url
        self.timeout = timeout
        self.session_id: str | None = None
        self._client = httpx.Client(timeout=timeout)

    def _headers(self) -> dict:
        h = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if self.session_id:
            h["Mcp-Session-Id"] = self.session_id
        return h

    def _post(self, payload: dict) -> dict:
        resp = self._client.post(self.url, headers=self._headers(), json=payload)
        # Capture session ID from response headers
        sid = resp.headers.get("mcp-session-id")
        if sid:
            self.session_id = sid
        resp.raise_for_status()
        # Handle SSE responses (text/event-stream)
        ct = resp.headers.get("content-type", "")
        if "text/event-stream" in ct:
            return self._parse_sse(resp.text)
        return resp.json()

    def _parse_sse(self, body: str) -> dict:
        """Extract the last JSON-RPC result from an SSE stream."""
        last_data = None
        for line in body.splitlines():
            if line.startswith("data: "):
                last_data = line[6:]
        if last_data:
            return json.loads(last_data)
        return {"error": "No data in SSE stream"}

    def initialize(self) -> dict:
        payload = jsonrpc(
            "initialize",
            {
                "clientInfo": {"name": "graphiti-cli", "version": "1.0"},
                "capabilities": {},
                "protocolVersion": PROTOCOL_VERSION,
            },
            req_id=0,
        )
        return self._post(payload)

    def call_tool(self, name: str, arguments: dict, req_id: int = 1) -> dict:
        payload = jsonrpc("tools/call", {"name": name, "arguments": arguments}, req_id)
        return self._post(payload)

    def list_tools(self) -> dict:
        payload = jsonrpc("tools/list", {"cursor": None})
        return self._post(payload)

    def connect(self):
        """Initialize session, required before any tool calls."""
        result = self.initialize()
        if "error" in result:
            print(f"Error initializing: {result['error']}", file=sys.stderr)
            sys.exit(1)
        return result


def extract_result(response: dict) -> str:
    """Extract text content from a tool call response."""
    if "error" in response:
        return f"Error: {json.dumps(response['error'], indent=2)}"
    result = response.get("result", {})
    if result.get("isError"):
        contents = result.get("content", [])
        texts = [c.get("text", "") for c in contents if c.get("type") == "text"]
        return f"Tool error: {' '.join(texts)}"
    contents = result.get("content", [])
    texts = [c.get("text", "") for c in contents if c.get("type") == "text"]
    return "\n".join(texts) if texts else json.dumps(result, indent=2)


def pretty_print(text: str, as_json: bool = False):
    """Try to pretty-print JSON, fall back to plain text."""
    if as_json:
        try:
            data = json.loads(text)
            print(json.dumps(data, indent=2))
            return
        except (json.JSONDecodeError, TypeError):
            pass
    print(text)


def cmd_status(client: GraphitiClient, args):
    client.connect()
    resp = client.call_tool("get_status", {})
    pretty_print(extract_result(resp), as_json=True)


def cmd_add(client: GraphitiClient, args):
    client.connect()
    arguments = {
        "name": args.name,
        "episode_body": args.body,
        "source": args.source,
        "source_description": args.desc,
    }
    resp = client.call_tool("add_episode", arguments)
    text = extract_result(resp)
    print(text)


def cmd_search(client: GraphitiClient, args):
    client.connect()
    arguments = {"query": args.query}
    if args.group:
        arguments["group_ids"] = [args.group]
    resp = client.call_tool("search_nodes", arguments)
    pretty_print(extract_result(resp), as_json=True)


def cmd_facts(client: GraphitiClient, args):
    client.connect()
    arguments = {"query": args.query}
    if args.group:
        arguments["group_ids"] = [args.group]
    resp = client.call_tool("search_facts", arguments)
    pretty_print(extract_result(resp), as_json=True)


def cmd_episodes(client: GraphitiClient, args):
    client.connect()
    arguments = {
        "group_id": args.group,
        "limit": args.limit,
    }
    resp = client.call_tool("get_episodes", arguments)
    pretty_print(extract_result(resp), as_json=True)


def cmd_delete_episode(client: GraphitiClient, args):
    client.connect()
    resp = client.call_tool("delete_episode", {"episode_id": args.episode_id})
    print(extract_result(resp))


def cmd_tools(client: GraphitiClient, args):
    client.connect()
    resp = client.list_tools()
    result = resp.get("result", {})
    tools = result.get("tools", [])
    if not tools:
        print("No tools found")
        return
    for tool in tools:
        name = tool.get("name", "?")
        desc = tool.get("description", "")
        desc_short = textwrap.shorten(desc, width=80, placeholder="...")
        schema = tool.get("inputSchema", {})
        required = schema.get("required", [])
        props = list(schema.get("properties", {}).keys())
        print(f"  {name}")
        print(f"    {desc_short}")
        print(f"    args: {', '.join(props)}  required: {', '.join(required)}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Graphiti knowledge graph CLI (MCP-over-HTTP)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--url",
        default=DEFAULT_URL,
        help=f"Graphiti MCP server URL (default: {DEFAULT_URL})",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=30.0,
        help="HTTP timeout in seconds (default: 30)",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # status
    sub.add_parser("status", help="Check server health")

    # add
    p_add = sub.add_parser("add", help="Add a memory/episode")
    p_add.add_argument("name", help="Episode name/title")
    p_add.add_argument("body", help="Episode body content")
    p_add.add_argument(
        "--source",
        default="text",
        choices=["text", "json", "message"],
        help="Source type (default: text)",
    )
    p_add.add_argument(
        "--desc", default="cli entry", help="Source description (default: 'cli entry')"
    )

    # search
    p_search = sub.add_parser("search", help="Search entity nodes")
    p_search.add_argument("query", help="Search query")
    p_search.add_argument("--group", default=None, help="Filter by group ID")

    # facts
    p_facts = sub.add_parser("facts", help="Search facts/relationships")
    p_facts.add_argument("query", help="Search query")
    p_facts.add_argument("--group", default=None, help="Filter by group ID")

    # episodes
    p_ep = sub.add_parser("episodes", help="Get recent episodes")
    p_ep.add_argument(
        "--limit", type=int, default=10, help="Max episodes (default: 10)"
    )
    p_ep.add_argument(
        "--group", default=DEFAULT_GROUP, help=f"Group ID (default: {DEFAULT_GROUP})"
    )

    # delete-episode
    p_del = sub.add_parser("delete-episode", help="Delete an episode by ID")
    p_del.add_argument("episode_id", help="Episode UUID to delete")

    # tools
    sub.add_parser("tools", help="List available server tools")

    args = parser.parse_args()
    client = GraphitiClient(url=args.url, timeout=args.timeout)

    commands = {
        "status": cmd_status,
        "add": cmd_add,
        "search": cmd_search,
        "facts": cmd_facts,
        "episodes": cmd_episodes,
        "delete-episode": cmd_delete_episode,
        "tools": cmd_tools,
    }

    try:
        commands[args.command](client, args)
    except httpx.ConnectError:
        print("Error: Cannot connect to Graphiti server at", args.url, file=sys.stderr)
        print("Check that Neo4j and Graphiti services are running:", file=sys.stderr)
        print("  launchctl list | grep claude", file=sys.stderr)
        sys.exit(1)
    except httpx.HTTPStatusError as e:
        print(
            f"HTTP error: {e.response.status_code} {e.response.text}", file=sys.stderr
        )
        sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(130)


if __name__ == "__main__":
    main()
