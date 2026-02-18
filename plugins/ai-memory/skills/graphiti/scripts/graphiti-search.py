#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx"]
# ///
"""Search the Graphiti knowledge graph via HTTP. Queries nodes and facts.

Usage:
  uv run graphiti-search.py "kubernetes deployment issues"
  uv run graphiti-search.py --facts "nix build errors"
  uv run graphiti-search.py --group nix-dotfiles "common issues"
  uv run graphiti-search.py --both "api authentication"
"""
import argparse
import json
import sys

import httpx

DEFAULT_URL = "http://127.0.0.1:51847/mcp/"
PROTOCOL_VERSION = "2025-03-26"


def mcp_request(
    client: httpx.Client,
    url: str,
    session_id: str | None,
    method: str,
    params: dict,
    req_id: int = 1,
) -> tuple[dict, str | None]:
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    if session_id:
        headers["Mcp-Session-Id"] = session_id

    payload = {"jsonrpc": "2.0", "id": req_id, "method": method, "params": params}
    resp = client.post(url, headers=headers, json=payload)
    new_sid = resp.headers.get("mcp-session-id", session_id)
    resp.raise_for_status()

    ct = resp.headers.get("content-type", "")
    if "text/event-stream" in ct:
        last_data = None
        for line in resp.text.splitlines():
            if line.startswith("data: "):
                last_data = line[6:]
        if last_data:
            return json.loads(last_data), new_sid
        return {"error": "Empty SSE stream"}, new_sid
    return resp.json(), new_sid


def extract_text(resp: dict) -> str:
    result = resp.get("result", {})
    if result.get("isError"):
        contents = result.get("content", [])
        texts = [c.get("text", "") for c in contents if c.get("type") == "text"]
        return f"Error: {' '.join(texts)}"
    contents = result.get("content", [])
    texts = [c.get("text", "") for c in contents if c.get("type") == "text"]
    return "\n".join(texts) if texts else ""


def pretty_json(text: str) -> str:
    try:
        data = json.loads(text)
        return json.dumps(data, indent=2)
    except (json.JSONDecodeError, TypeError):
        return text


def main():
    parser = argparse.ArgumentParser(
        description="Search Graphiti knowledge graph",
    )
    parser.add_argument("query", help="Search query")
    parser.add_argument("--url", default=DEFAULT_URL, help="Graphiti server URL")

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--nodes",
        action="store_true",
        default=True,
        help="Search entity nodes (default)",
    )
    mode.add_argument("--facts", action="store_true", help="Search facts/relationships")
    mode.add_argument(
        "--both",
        action="store_true",
        help="Search both nodes and facts",
    )

    parser.add_argument("--group", default=None, help="Filter by group ID")
    parser.add_argument(
        "--raw", action="store_true", help="Output raw JSON without formatting"
    )

    args = parser.parse_args()

    try:
        client = httpx.Client(timeout=30.0)

        # Initialize session
        init_resp, session_id = mcp_request(
            client,
            args.url,
            None,
            "initialize",
            {
                "clientInfo": {"name": "graphiti-search", "version": "1.0"},
                "capabilities": {},
                "protocolVersion": PROTOCOL_VERSION,
            },
            req_id=0,
        )

        if "error" in init_resp:
            print(f"Init error: {init_resp['error']}", file=sys.stderr)
            sys.exit(1)

        search_nodes = args.both or (not args.facts)
        search_facts = args.both or args.facts

        req_id = 1

        if search_nodes:
            arguments: dict = {"query": args.query}
            if args.group:
                arguments["group_ids"] = [args.group]

            resp, session_id = mcp_request(
                client,
                args.url,
                session_id,
                "tools/call",
                {"name": "search_nodes", "arguments": arguments},
                req_id=req_id,
            )
            req_id += 1

            text = extract_text(resp)
            if args.both:
                print("=== Nodes ===")
            if args.raw:
                print(text)
            else:
                print(pretty_json(text))

        if search_facts:
            arguments = {"query": args.query}
            if args.group:
                arguments["group_ids"] = [args.group]

            resp, session_id = mcp_request(
                client,
                args.url,
                session_id,
                "tools/call",
                {"name": "search_facts", "arguments": arguments},
                req_id=req_id,
            )

            text = extract_text(resp)
            if args.both:
                print("\n=== Facts ===")
            if args.raw:
                print(text)
            else:
                print(pretty_json(text))

    except httpx.ConnectError:
        print(f"Error: Cannot connect to {args.url}", file=sys.stderr)
        print("Start services: launchctl list | grep claude", file=sys.stderr)
        sys.exit(1)
    except httpx.HTTPStatusError as e:
        print(f"HTTP {e.response.status_code}: {e.response.text}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
