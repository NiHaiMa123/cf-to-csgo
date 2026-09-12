#!/usr/bin/env python3
"""Send one Blender MCP JSON-over-TCP command and print the response."""
from __future__ import annotations

import argparse
import json
import socket
import sys
from pathlib import Path


def call(command: str, params: dict, host: str, port: int, timeout: float) -> dict:
    request = json.dumps({"type": command, "params": params}, ensure_ascii=False).encode()
    with socket.create_connection((host, port), timeout=timeout) as sock:
        sock.settimeout(timeout)
        sock.sendall(request)
        payload = bytearray()
        while True:
            try:
                chunk = sock.recv(65536)
            except socket.timeout as exc:
                raise TimeoutError(f"blender MCP timeout after {timeout}s; partial={payload[:200]!r}") from exc
            if not chunk:
                break
            payload.extend(chunk)
            try:
                return json.loads(payload)
            except json.JSONDecodeError:
                continue
    raise RuntimeError(f"blender MCP closed without JSON: {payload[:500]!r}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command")
    parser.add_argument("--params-file")
    parser.add_argument("--code-file")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9876)
    parser.add_argument("--timeout", type=float, default=60.0)
    args = parser.parse_args()
    params: dict = {}
    if args.params_file:
        params = json.loads(Path(args.params_file).read_text(encoding="utf-8"))
    if args.code_file:
        params["code"] = Path(args.code_file).read_text(encoding="utf-8")
    response = call(args.command, params, args.host, args.port, args.timeout)
    json.dump(response, sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0 if response.get("status") == "success" else 1


if __name__ == "__main__":
    raise SystemExit(main())
