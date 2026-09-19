import socket, json, sys

path = sys.argv[1] if len(sys.argv) > 1 else r'D:\project\cf_to_csgo\work\galil_ace_tianxi\effects\probes\blender_check.py'
code = open(path, encoding='utf-8').read()

s = socket.create_connection(('127.0.0.1', 9876), timeout=10)
cmd = {'type': 'execute_code', 'params': {'code': code}}
s.sendall(json.dumps(cmd).encode())
s.settimeout(300)
resp = b''
while True:
    try:
        chunk = s.recv(65536)
        if not chunk:
            break
        resp += chunk
        try:
            json.loads(resp)
            break
        except Exception:
            continue
    except socket.timeout:
        break
try:
    print(json.dumps(json.loads(resp), indent=2)[:4000])
except Exception:
    print(resp[:4000])
s.close()
