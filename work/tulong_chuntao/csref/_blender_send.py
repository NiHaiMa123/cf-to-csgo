# -*- coding: utf-8 -*-
"""Send a python file to blender-mcp (localhost:9876) execute_code and print result."""
import json
import socket
import sys


def main() -> int:
    code = open(sys.argv[1], encoding="utf-8").read()
    s = socket.create_connection(("127.0.0.1", 9876), timeout=300)
    s.sendall(json.dumps({"type": "execute_code",
                          "params": {"code": code}}).encode())
    s.settimeout(300)
    buf = b""
    # server sends exactly one JSON response then waits; read until it parses
    while True:
        chunk = s.recv(65536)
        if not chunk:
            break
        buf += chunk
        try:
            json.loads(buf)
            break
        except json.JSONDecodeError:
            continue
    s.close()
    try:
        r = json.loads(buf)
        res = r.get("result", {})
        print(r.get("status"), res.get("message", ""))
        out = res.get("output") or res.get("result")
        if out:
            print("OUTPUT:", str(out)[:4000])
        err = res.get("error") or res.get("traceback")
        if err:
            print("ERR:", str(err)[:3000])
    except Exception:
        print("RAW:", buf[:2000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
