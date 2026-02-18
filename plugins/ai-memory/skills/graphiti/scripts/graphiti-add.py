#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx"]
# ///
"""Store a memory in Graphiti via HTTP. Designed for hooks and automation.

Usage:
  uv run graphiti-add.py "Fix: YAML parse error" "Problem: wrong keys. Solution: use correct schema."
  uv run graphiti-add.py --source json "Config: api-server" '{"port": 8080, "replicas": 3}'
  uv run graphiti-add.py --desc "deployment record" "Deploy: api v2.1" "Deployed api to prod-cluster/default"
  echo "body text" | uv run graphiti-add.py --stdin "Episode Title"
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


def main():
    parser = argparse.ArgumentParser(
        description="Store a memory in Graphiti knowledge graph",
    )
    parser.add_argument("name", help="Episode name/title")
    parser.add_argument("body", nargs="?", default=None, help="Episode body content")
    parser.add_argument(
        "--stdin",
        action="store_true",
        help="Read body from stdin instead of argument",
    )
    parser.add_argument(
        "--source",
        default="text",
        choices=["text", "json", "message"],
        help="Source type (default: text)",
    )
    parser.add_argument(
        "--desc",
        default="cli entry",
        help="Source description (default: 'cli entry')",
    )
    parser.add_argument("--url", default=DEFAULT_URL, help="Graphiti server URL")
    parser.add_argument(
        "--quiet", "-q", action="store_true", help="Suppress output on success"
    )

    args = parser.parse_args()

    body = args.body
    if args.stdin or body is None:
        body = sys.stdin.read().strip()
    if not body:
        print("Error: no body provided (use argument or --stdin)", file=sys.stderr)
        sys.exit(1)

    try:
        client = httpx.Client(timeout=30.0)

        # Initialize session
        init_resp, session_id = mcp_request(
            client,
            args.url,
            None,
            "initialize",
            {
                "clientInfo": {"name": "graphiti-add", "version": "1.0"},
                "capabilities": {},
                "protocolVersion": PROTOCOL_VERSION,
            },
            req_id=0,
        )

        if "error" in init_resp:
            print(f"Init error: {init_resp['error']}", file=sys.stderr)
            sys.exit(1)

        # Add episode
        resp, _ = mcp_request(
            client,
            args.url,
            session_id,
            "tools/call",
            {
                "name": "add_episode",
                "arguments": {
                    "name": args.name,
                    "episode_body": body,
                    "source": args.source,
                    "source_description": args.desc,
                },
            },
        )

        result = resp.get("result", {})
        if result.get("isError"):
            contents = result.get("content", [])
            texts = [c.get("text", "") for c in contents if c.get("type") == "text"]
            print(f"Error: {' '.join(texts)}", file=sys.stderr)
            sys.exit(1)

        if not args.quiet:
            contents = result.get("content", [])
            texts = [c.get("text", "") for c in contents if c.get("type") == "text"]
            print("\n".join(texts) if texts else "Episode added")

    except httpx.ConnectError:
        print(f"Error: Cannot connect to {args.url}", file=sys.stderr)
        print("Start services: launchctl list | grep claude", file=sys.stderr)
        sys.exit(1)
    except httpx.HTTPStatusError as e:
        print(f"HTTP {e.response.status_code}: {e.response.text}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
