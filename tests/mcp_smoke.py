"""Exercise the installed Codex MCP configuration without starting an agent session."""
import json
from pathlib import Path
import queue
import subprocess
import sys
import threading

root = Path(sys.argv[1]).resolve()
config = json.loads((root / '.mcp.codex.json').read_text(encoding='utf-8'))['mcpServers']['al']
proc = subprocess.Popen(
    [config['command'], *config['args']], cwd=root / config['cwd'],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    text=True, encoding='utf-8',
)
messages = queue.Queue()
errors = []

def read_output():
    for line in proc.stdout:
        try:
            messages.put(json.loads(line))
        except json.JSONDecodeError:
            messages.put({'invalid_stdout': line.rstrip()})

def read_errors():
    errors.extend(proc.stderr)

threading.Thread(target=read_output, daemon=True).start()
threading.Thread(target=read_errors, daemon=True).start()

def send(message):
    proc.stdin.write(json.dumps(message) + '\n')
    proc.stdin.flush()

def receive(request_id):
    while True:
        result = messages.get(timeout=30)
        if 'invalid_stdout' in result:
            raise AssertionError(result)
        if result.get('id') == request_id:
            if 'error' in result:
                raise AssertionError(result)
            return result['result']

try:
    send({'jsonrpc': '2.0', 'id': 1, 'method': 'initialize', 'params': {
        'protocolVersion': '2024-11-05', 'capabilities': {},
        'clientInfo': {'name': 'codex-al-toolkit-smoke', 'version': '1.0.0'},
    }})
    receive(1)
    send({'jsonrpc': '2.0', 'method': 'notifications/initialized'})
    send({'jsonrpc': '2.0', 'id': 2, 'method': 'tools/list', 'params': {}})
    names = {tool['name'] for tool in receive(2)['tools']}
    required = {'al_addproject', 'al_compile', 'al_getdiagnostics', 'al_symbolsearch'}
    assert required <= names, f'Missing AL tools: {required - names}; available: {sorted(names)}'
    print(f'PASS: cached MCP initializes over STDIO and exposes {len(names)} AL tools')
finally:
    proc.stdin.close()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        subprocess.run(['taskkill', '/PID', str(proc.pid), '/T', '/F'], capture_output=True)
        proc.wait(timeout=10)
    if proc.returncode:
        print(''.join(errors), file=sys.stderr)