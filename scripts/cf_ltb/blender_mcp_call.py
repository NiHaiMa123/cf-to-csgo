#!/usr/bin/env python3
"""Minimal JSON-over-TCP client for the local Blender MCP addon."""
from __future__ import annotations

import argparse
import json
import socket
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command")
    parser.add_argument("--params", default="{}")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9876)
    parser.add_argument("--timeout", type=float, default=20.0)
    args = parser.parse_args()
    params = json.loads(args.params)
    request = json.dumps({"type": args.command, "params": params}, ensure_ascii=False).encode()
    with socket.create_connection((args.host, args.port), timeout=args.timeout) as sock:
        sock.settimeout(args.timeout)
        sock.sendall(request)
        payload = bytearray()
        while True:
            try:
                chunk = sock.recv(65536)
            except socket.timeout:
                break
            if not chunk:
                break
            payload.extend(chunk)
            try:
                response = json.loads(payload)
            except json.JSONDecodeError:
                continue
            print(json.dumps(response, ensure_ascii=False, indent=2))
            return 0 if response.get("status") == "success" else 1
    print(payload.decode(errors="replace"))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
