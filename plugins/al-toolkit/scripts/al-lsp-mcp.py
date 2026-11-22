#!/usr/bin/env python3
"""MCP stdio bridge and CLI wrapper for the AL Language Server (al-lsp.cmd).

Exposes 7 semantic AL code-intelligence tools over MCP (protocolVersion
"2024-11-05", newline-delimited JSON-RPC over stdin/stdout) as well as a
single-shot `--cli <tool_name> <json_args_string_or_file>` mode.

Uses Python 3 standard library only. All diagnostics go to stderr.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

PROTOCOL_VERSION = "2024-11-05"
SERVER_INFO = {"name": "al-lsp-mcp", "version": "1.0.0"}

DEFAULT_INIT_TIMEOUT = float(os.environ.get("AL_LSP_INIT_TIMEOUT", "60"))
DEFAULT_REQUEST_TIMEOUT = float(os.environ.get("AL_LSP_TIMEOUT", "30"))
DEFAULT_RENAME_TIMEOUT = float(os.environ.get("AL_LSP_RENAME_TIMEOUT", "15"))

SYMBOL_KINDS = {
    1: "File",
    2: "Module",
    3: "Namespace",
    4: "Package",
    5: "Class",
    6: "Method",
    7: "Property",
    8: "Field",
    9: "Constructor",
    10: "Enum",
    11: "Interface",
    12: "Function",
    13: "Variable",
    14: "Constant",
    15: "String",
    16: "Number",
    17: "Boolean",
    18: "Array",
    19: "Object",
    20: "Key",
    21: "Null",
    22: "EnumMember",
    23: "Struct",
    24: "Event",
    25: "Operator",
    26: "TypeParameter",
}

SKIP_WALK_DIRS = frozenset({
    ".git",
    ".alpackages",
    ".vscode",
    ".snapshots",
    ".vs",
    "bin",
    "obj",
    "node_modules",
})

TOOLS: list[dict[str, Any]] = [
    {
        "name": "al_lsp_definition",
        "description": (
            "Resolve the definition location(s) of the AL symbol at a 1-based "
            "line and character position in a file."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "filePath": {
                    "type": "string",
                    "description": "Path to the .al file.",
                },
                "line": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "1-based line number.",
                },
                "character": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "1-based character/column number.",
                },
                "projectPath": {
                    "type": "string",
                    "description": (
                        "Optional AL project or workspace folder path. If omitted, "
                        "resolved by walking up from filePath."
                    ),
                },
            },
            "required": ["filePath", "line", "character"],
            "additionalProperties": False,
        },
    },
    {
        "name": "al_lsp_references",
        "description": (
            "Find all semantic references across the AL project/workspace to the "
            "symbol at a 1-based line and character position (skips comments and strings)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "filePath": {
                    "type": "string",
                    "description": "Path to the .al file.",
                },
                "line": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "1-based line number.",
                },
                "character": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "1-based character/column number.",
                },
                "includeDeclaration": {
                    "type": "boolean",
                    "default": True,
                    "description": "Whether to include the symbol declaration (default true).",
                },
                "projectPath": {
                    "type": "string",
                    "description": "Optional AL project or workspace folder path.",
                },
            },
            "required": ["filePath", "line", "character"],
            "additionalProperties": False,
        },
    },
    {
        "name": "al_lsp_hover",
        "description": (
            "Get AL type signature, XML doc comments, and hover documentation for "
            "the symbol at a 1-based line and character position."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "filePath": {
                    "type": "string",
                    "description": "Path to the .al file.",
                },
                "line": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "1-based line number.",
                },
                "character": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "1-based character/column number.",
                },
                "projectPath": {
                    "type": "string",
                    "description": "Optional AL project or workspace folder path.",
                },
            },
            "required": ["filePath", "line", "character"],
            "additionalProperties": False,
        },
    },
    {
        "name": "al_lsp_document_symbols",
        "description": (
            "List the hierarchical symbols (objects, fields, keys, triggers, "
            "procedures) in an .al file with 1-based line/character ranges."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "filePath": {
                    "type": "string",
                    "description": "Path to the .al file.",
                },
                "projectPath": {
                    "type": "string",
                    "description": "Optional AL project or workspace folder path.",
                },
            },
            "required": ["filePath"],
            "additionalProperties": False,
        },
    },
    {
        "name": "al_lsp_workspace_symbols",
        "description": (
            "Search AL objects, procedures, and symbols across the loaded "
            "workspace by query string."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Symbol name or substring query.",
                },
                "projectPath": {
                    "type": "string",
                    "description": "Optional AL project or workspace folder path.",
                },
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
    {
        "name": "al_lsp_signature_help",
        "description": (
            "Get procedure overload signatures, parameter documentation, and "
            "active parameter info at a 1-based call-site position."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "filePath": {
                    "type": "string",
                    "description": "Path to the .al file.",
                },
                "line": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "1-based line number inside a procedure call.",
                },
                "character": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "1-based character/column number.",
                },
                "projectPath": {
                    "type": "string",
                    "description": "Optional AL project or workspace folder path.",
                },
            },
            "required": ["filePath", "line", "character"],
            "additionalProperties": False,
        },
    },
    {
        "name": "al_lsp_rename_preview",
        "description": (
            "Compute a non-destructive rename preview (workspace edits) for an AL "
            "symbol at a 1-based position without modifying files on disk."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "filePath": {
                    "type": "string",
                    "description": "Path to the .al file.",
                },
                "line": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "1-based line number.",
                },
                "character": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "1-based character/column number.",
                },
                "newName": {
                    "type": "string",
                    "description": "Proposed new symbol name.",
                },
                "projectPath": {
                    "type": "string",
                    "description": "Optional AL project or workspace folder path.",
                },
            },
            "required": ["filePath", "line", "character", "newName"],
            "additionalProperties": False,
        },
    },
]


def log_err(message: str) -> None:
    """Write a diagnostic message to stderr."""
    sys.stderr.write(f"[al-lsp-mcp] {message}\n")
    sys.stderr.flush()


def read_text_utf8(path: Path) -> str:
    """Read a text file as UTF-8, stripping any UTF-8 BOM."""
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        return raw.decode("utf-8-sig")
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("utf-8-sig", errors="replace")


def uri_to_path(uri: str) -> str:
    """Convert a file:// URI to a local filesystem path; keep non-file URIs verbatim."""
    if not uri:
        return ""
    parsed = urllib.parse.urlparse(uri)
    if parsed.scheme.lower() == "file":
        local = urllib.request.url2pathname(parsed.path)
        if parsed.netloc:
            return f"\\\\{parsed.netloc}{local}"
        return local
    return uri


def path_to_uri(path: Path) -> str:
    """Convert a filesystem Path to an LSP file:// URI."""
    return path.resolve().as_uri()


def get_line_preview(
    file_path: str,
    zero_based_line: int,
    line_cache: dict[str, list[str]],
) -> str:
    """Read the source line for a 0-based line number from disk (cached per call)."""
    if not file_path or zero_based_line < 0:
        return ""
    lines = line_cache.get(file_path)
    if lines is None:
        if os.path.isfile(file_path):
            try:
                lines = read_text_utf8(Path(file_path)).splitlines()
            except OSError:
                lines = []
        else:
            lines = []
        line_cache[file_path] = lines
    if 0 <= zero_based_line < len(lines):
        return lines[zero_based_line].strip()
    return ""


def convert_range_to_location(
    uri: str,
    lsp_range: dict[str, Any],
    line_cache: dict[str, list[str]],
) -> dict[str, Any]:
    """Convert a 0-based LSP URI+range to a 1-based location dict with line preview."""
    file_path = uri_to_path(uri)
    start = lsp_range.get("start") or {}
    end = lsp_range.get("end") or {}
    s_line = int(start.get("line", 0))
    s_char = int(start.get("character", 0))
    e_line = int(end.get("line", s_line))
    e_char = int(end.get("character", s_char))
    return {
        "filePath": file_path,
        "startLine": s_line + 1,
        "startCharacter": s_char + 1,
        "endLine": e_line + 1,
        "endCharacter": e_char + 1,
        "preview": get_line_preview(file_path, s_line, line_cache),
    }


def extract_markup_text(value: Any) -> str:
    """Normalize LSP MarkupContent, MarkedString, or list of MarkedStrings to text."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value.replace("\r\n", "\n").strip()
    if isinstance(value, dict):
        text = value.get("value", "")
        lang = value.get("language")
        cleaned = str(text).replace("\r\n", "\n").strip()
        if lang and cleaned:
            return f"```{lang}\n{cleaned}\n```"
        return cleaned
    if isinstance(value, list):
        parts = [extract_markup_text(item) for item in value]
        return "\n\n".join(part for part in parts if part)
    return str(value)


def require_positive_int(args: dict[str, Any], key: str) -> int:
    """Validate and return a 1-based positive integer argument."""
    if key not in args:
        raise ValueError(f"Missing required parameter: {key}")
    val = args[key]
    if isinstance(val, bool) or not isinstance(val, int) or val < 1:
        raise ValueError(f"Parameter '{key}' must be a 1-based integer >= 1, got {val!r}")
    return val


def require_string(args: dict[str, Any], key: str, allow_empty: bool = False) -> str:
    """Validate and return a string argument."""
    if key not in args:
        raise ValueError(f"Missing required parameter: {key}")
    val = args[key]
    if not isinstance(val, str):
        raise ValueError(f"Parameter '{key}' must be a string, got {type(val).__name__}")
    if not allow_empty and not val.strip():
        raise ValueError(f"Parameter '{key}' must be a non-empty string")
    return val


def resolve_file_path(file_path_raw: str, project_path: str | None = None) -> Path:
    """Resolve an input filePath against CWD or projectPath and verify it exists."""
    candidate = Path(file_path_raw.strip()).expanduser()
    if not candidate.is_absolute() and not candidate.exists():
        if project_path:
            proj = Path(project_path.strip()).expanduser()
            if proj.is_file():
                proj = proj.parent
            alt = proj / candidate
            if alt.exists():
                candidate = alt
    resolved = candidate.resolve()
    if not resolved.is_file():
        raise FileNotFoundError(f"File not found: {resolved}")
    return resolved


def resolve_project_root(
    project_path: str | None = None,
    file_path: Path | None = None,
) -> str:
    """Determine the AL project/workspace root from args, file ancestors, env, or CWD."""
    if isinstance(project_path, str) and project_path.strip():
        p = Path(project_path.strip()).expanduser().resolve()
        if p.is_file():
            p = p.parent
        return str(p)

    if file_path is not None:
        start = file_path if file_path.is_dir() else file_path.parent
        for directory in (start, *start.parents):
            if not directory.is_dir():
                continue
            if (directory / "app.json").is_file() or any(directory.glob("*.code-workspace")):
                return str(directory)

    env_dir = os.environ.get("AL_PROJECT_DIR", "").strip()
    if env_dir:
        p = Path(env_dir).expanduser().resolve()
        if p.is_file():
            p = p.parent
        return str(p)

    return str(Path(os.getcwd()).resolve())


def find_first_al_file(project_root: str) -> Path | None:
    """Locate one .al file under project_root so cold workspace/symbol queries index."""
    root = Path(project_root)
    if not root.is_dir():
        return None
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_WALK_DIRS)
        for name in sorted(filenames):
            if name.lower().endswith(".al"):
                return Path(dirpath) / name
    return None


class LspSession:
    """Manages one `cmd /c al-lsp.cmd` subprocess and its LSP stdio stream."""

    def __init__(self, al_lsp_cmd: str, project_root: str) -> None:
        self.al_lsp_cmd = al_lsp_cmd
        self.project_root = project_root
        self._write_lock = threading.Lock()
        self._pending_lock = threading.Lock()
        self._pending: dict[int, dict[str, Any]] = {}
        self._next_id = 0
        self._closed = False
        self._eof_error: str | None = None
        self.opened_files: dict[str, tuple[int, str]] = {}
        self.notifications: list[dict[str, Any]] = []
        self.server_capabilities: dict[str, Any] = {}

        if not os.path.isfile(al_lsp_cmd):
            raise FileNotFoundError(f"al-lsp.cmd not found at: {al_lsp_cmd}")

        env = os.environ.copy()
        env["AL_PROJECT_DIR"] = project_root
        cwd = project_root if os.path.isdir(project_root) else None

        log_err(f"Starting AL LSP server for project: {project_root}")
        self.proc = subprocess.Popen(
            ["cmd", "/c", al_lsp_cmd],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            cwd=cwd,
        )

        self._stdout_thread = threading.Thread(
            target=self._read_stdout_loop,
            name="al-lsp-stdout",
            daemon=True,
        )
        self._stderr_thread = threading.Thread(
            target=self._read_stderr_loop,
            name="al-lsp-stderr",
            daemon=True,
        )
        self._stdout_thread.start()
        self._stderr_thread.start()

        try:
            self._initialize()
        except Exception:
            self.shutdown()
            raise

    def is_alive(self) -> bool:
        """Return True if the LSP subprocess is running and stdout is open."""
        return not self._closed and self.proc.poll() is None

    def _send_raw(self, message: dict[str, Any]) -> None:
        """Frame and write a JSON-RPC message with Content-Length header."""
        if self._closed or self.proc.stdin is None:
            raise RuntimeError(self._eof_error or "AL LSP server stdin is closed")
        body = json.dumps(message, ensure_ascii=False).encode("utf-8")
        frame = f"Content-Length: {len(body)}\r\n\r\n".encode("ascii") + body
        with self._write_lock:
            try:
                self.proc.stdin.write(frame)
                self.proc.stdin.flush()
            except OSError as exc:
                raise RuntimeError(f"Failed writing to AL LSP server: {exc}") from exc

    def _read_stderr_loop(self) -> None:
        """Drain subprocess stderr and forward to our stderr."""
        assert self.proc.stderr is not None
        try:
            while True:
                line = self.proc.stderr.readline()
                if not line:
                    break
                sys.stderr.buffer.write(line)
                sys.stderr.buffer.flush()
        except OSError:
            pass

    def _read_stdout_loop(self) -> None:
        """Read Content-Length framed JSON-RPC messages from the LSP server."""
        assert self.proc.stdout is not None
        try:
            while True:
                headers: dict[str, str] = {}
                while True:
                    line = self.proc.stdout.readline()
                    if not line:
                        self._fail_pending("AL LSP server closed stdout unexpectedly")
                        return
                    if line in (b"\r\n", b"\n"):
                        if headers:
                            break
                        continue
                    key, sep, val = line.decode("ascii", errors="replace").partition(":")
                    if sep:
                        headers[key.strip().lower()] = val.strip()

                cl_str = headers.get("content-length")
                if not cl_str:
                    continue
                content_length = int(cl_str)
                chunks = []
                remaining = content_length
                while remaining > 0:
                    chunk = self.proc.stdout.read(remaining)
                    if not chunk:
                        self._fail_pending("AL LSP server closed stdout mid-message")
                        return
                    chunks.append(chunk)
                    remaining -= len(chunk)

                payload = b"".join(chunks).decode("utf-8", errors="replace")
                try:
                    msg = json.loads(payload)
                except json.JSONDecodeError as exc:
                    log_err(f"Invalid JSON from LSP server: {exc}")
                    continue

                self._dispatch_message(msg)
        except Exception as exc:
            self._fail_pending(f"LSP stdout reader error: {exc}")

    def _fail_pending(self, reason: str) -> None:
        """Mark session closed and wake any threads waiting for LSP responses."""
        self._closed = True
        self._eof_error = reason
        with self._pending_lock:
            for entry in self._pending.values():
                if entry["response"] is None:
                    entry["response"] = {"error": {"code": -32000, "message": reason}}
                entry["event"].set()

    def _dispatch_message(self, msg: dict[str, Any]) -> None:
        """Route an incoming LSP response, server request, or notification."""
        has_id = "id" in msg and msg["id"] is not None
        if has_id and ("result" in msg or "error" in msg):
            req_id = msg["id"]
            with self._pending_lock:
                entry = self._pending.get(req_id)
                if entry is not None:
                    entry["response"] = msg
                    entry["event"].set()
            return

        if has_id and "method" in msg:
            self._handle_server_request(msg)
            return

        # Server notification: keep bounded recent history
        self.notifications.append(msg)
        if len(self.notifications) > 200:
            del self.notifications[: len(self.notifications) - 200]

    def _handle_server_request(self, msg: dict[str, Any]) -> None:
        """Reply cleanly to server-initiated requests so the LSP server never blocks."""
        method = msg.get("method")
        req_id = msg["id"]
        result: Any = None
        if method == "workspace/configuration":
            items = (msg.get("params") or {}).get("items") or []
            result = [None] * len(items)
        try:
            self._send_raw({"jsonrpc": "2.0", "id": req_id, "result": result})
        except RuntimeError:
            pass

    def request(
        self,
        method: str,
        params: Any,
        timeout: float = DEFAULT_REQUEST_TIMEOUT,
    ) -> Any:
        """Send an LSP JSON-RPC request and wait for its correlated response."""
        if self._closed:
            raise RuntimeError(self._eof_error or "AL LSP server is not running")

        event = threading.Event()
        with self._pending_lock:
            self._next_id += 1
            req_id = self._next_id
            self._pending[req_id] = {"event": event, "response": None}

        try:
            self._send_raw({
                "jsonrpc": "2.0",
                "id": req_id,
                "method": method,
                "params": params,
            })
        except Exception:
            with self._pending_lock:
                self._pending.pop(req_id, None)
            raise

        if not event.wait(timeout):
            with self._pending_lock:
                self._pending.pop(req_id, None)
            try:
                self.notify("$/cancelRequest", {"id": req_id})
            except Exception:
                pass
            raise TimeoutError(
                f"AL LSP server did not respond to '{method}' within {timeout:g}s"
            )

        with self._pending_lock:
            entry = self._pending.pop(req_id, None)
        response = (entry or {}).get("response") or {}
        if "error" in response and response["error"] is not None:
            err = response["error"]
            msg = err.get("message") if isinstance(err, dict) else str(err)
            code = err.get("code") if isinstance(err, dict) else None
            raise RuntimeError(f"AL LSP '{method}' failed ({code}): {msg}")
        return response.get("result")

    def notify(self, method: str, params: Any) -> None:
        """Send an LSP JSON-RPC notification."""
        self._send_raw({"jsonrpc": "2.0", "method": method, "params": params})

    def _initialize(self) -> None:
        """Perform the LSP initialize / initialized handshake."""
        root_path = Path(self.project_root).resolve()
        root_uri = root_path.as_uri()
        init_params = {
            "processId": os.getpid(),
            "rootUri": root_uri,
            "workspaceFolders": [
                {
                    "uri": root_uri,
                    "name": root_path.name or self.project_root,
                }
            ],
            "capabilities": {
                "textDocument": {
                    "synchronization": {
                        "dynamicRegistration": False,
                        "willSave": False,
                        "willSaveWaitUntil": False,
                        "didSave": False,
                    },
                    "definition": {
                        "dynamicRegistration": False,
                        "linkSupport": True,
                    },
                    "references": {
                        "dynamicRegistration": False,
                    },
                    "hover": {
                        "dynamicRegistration": False,
                        "contentFormat": ["markdown", "plaintext"],
                    },
                    "documentSymbol": {
                        "dynamicRegistration": False,
                        "hierarchicalDocumentSymbolSupport": True,
                    },
                    "signatureHelp": {
                        "dynamicRegistration": False,
                        "signatureInformation": {
                            "documentationFormat": ["markdown", "plaintext"],
                            "parameterInformation": {"labelOffsetSupport": True},
                        },
                    },
                    "rename": {
                        "dynamicRegistration": False,
                        "prepareSupport": False,
                    },
                },
                "workspace": {
                    "workspaceFolders": True,
                    "symbol": {"dynamicRegistration": False},
                    "workspaceEdit": {"documentChanges": True},
                },
            },
        }
        result = self.request("initialize", init_params, timeout=DEFAULT_INIT_TIMEOUT)
        if isinstance(result, dict):
            self.server_capabilities = result.get("capabilities") or {}
        self.notify("initialized", {})

    def ensure_open(self, file_path: Path) -> str:
        """Sync a file from disk to the LSP server via didOpen or didChange."""
        text = read_text_utf8(file_path)
        text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        uri = path_to_uri(file_path)

        existing = self.opened_files.get(uri)
        if existing is None:
            version = 1
            self.notify(
                "textDocument/didOpen",
                {
                    "textDocument": {
                        "uri": uri,
                        "languageId": "al",
                        "version": version,
                        "text": text,
                    }
                },
            )
            self.opened_files[uri] = (version, text_hash)
        elif existing[1] != text_hash:
            version = existing[0] + 1
            self.notify(
                "textDocument/didChange",
                {
                    "textDocument": {"uri": uri, "version": version},
                    "contentChanges": [{"text": text}],
                },
            )
            self.opened_files[uri] = (version, text_hash)

        return uri

    def shutdown(self) -> None:
        """Gracefully shut down the LSP server and clean up its process tree."""
        if not self._closed and self.proc.poll() is None:
            try:
                self.request("shutdown", None, timeout=3.0)
            except Exception:
                pass
            try:
                self.notify("exit", None)
            except Exception:
                pass
            try:
                self.proc.wait(timeout=3.0)
            except subprocess.TimeoutExpired:
                pass

        self._closed = True
        if self.proc.poll() is None:
            try:
                self.proc.terminate()
                self.proc.wait(timeout=2.0)
            except Exception:
                pass

        if self.proc.poll() is None:
            try:
                subprocess.run(
                    ["taskkill", "/F", "/T", "/PID", str(self.proc.pid)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=5.0,
                    check=False,
                )
            except Exception:
                try:
                    self.proc.kill()
                except Exception:
                    pass

        for pipe in (self.proc.stdin, self.proc.stdout, self.proc.stderr):
            if pipe is not None:
                try:
                    pipe.close()
                except OSError:
                    pass


def _convert_document_symbol(
    sym: dict[str, Any],
    file_path: str,
    line_cache: dict[str, list[str]],
) -> dict[str, Any]:
    """Convert a DocumentSymbol or SymbolInformation node to 1-based coordinates."""
    kind_num = int(sym.get("kind", 0))
    kind_name = SYMBOL_KINDS.get(kind_num, f"Kind({kind_num})")

    if "location" in sym:
        loc = sym["location"] or {}
        loc_uri = loc.get("uri") or ""
        loc_range = loc.get("range") or {}
        conv = convert_range_to_location(loc_uri, loc_range, line_cache)
        node: dict[str, Any] = {
            "name": sym.get("name", ""),
            "kind": kind_num,
            "kindName": kind_name,
            "containerName": sym.get("containerName", ""),
            "location": conv,
        }
        return node

    rng = sym.get("range") or {}
    sel = sym.get("selectionRange") or rng
    rng_start = rng.get("start") or {}
    rng_end = rng.get("end") or {}
    sel_start = sel.get("start") or rng_start
    sel_end = sel.get("end") or rng_end

    children_raw = sym.get("children") or []
    children = [_convert_document_symbol(c, file_path, line_cache) for c in children_raw]

    return {
        "name": sym.get("name", ""),
        "detail": sym.get("detail", ""),
        "kind": kind_num,
        "kindName": kind_name,
        "deprecated": bool(sym.get("deprecated", False)),
        "range": {
            "startLine": int(rng_start.get("line", 0)) + 1,
            "startCharacter": int(rng_start.get("character", 0)) + 1,
            "endLine": int(rng_end.get("line", 0)) + 1,
            "endCharacter": int(rng_end.get("character", 0)) + 1,
        },
        "selectionRange": {
            "startLine": int(sel_start.get("line", 0)) + 1,
            "startCharacter": int(sel_start.get("character", 0)) + 1,
            "endLine": int(sel_end.get("line", 0)) + 1,
            "endCharacter": int(sel_end.get("character", 0)) + 1,
            "preview": get_line_preview(
                file_path,
                int(sel_start.get("line", 0)),
                line_cache,
            ),
        },
        "children": children,
    }


def _convert_location_list(
    raw_result: Any,
    line_cache: dict[str, list[str]],
) -> list[dict[str, Any]]:
    """Normalize Location | Location[] | LocationLink[] | None into 1-based locations."""
    if raw_result is None:
        return []
    items = raw_result if isinstance(raw_result, list) else [raw_result]
    locations: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        if "targetUri" in item:
            uri = item.get("targetUri") or ""
            rng = item.get("targetSelectionRange") or item.get("targetRange") or {}
            locations.append(convert_range_to_location(uri, rng, line_cache))
        elif "uri" in item and "range" in item:
            locations.append(
                convert_range_to_location(item["uri"], item["range"], line_cache)
            )
    return locations


class LspManager:
    """Thread-safe coordinator managing a lazy LspSession across tool calls."""

    def __init__(self, al_lsp_cmd: str) -> None:
        self.al_lsp_cmd = al_lsp_cmd
        self._lock = threading.Lock()
        self._session: LspSession | None = None
        self._project_root_key: str | None = None

    def _get_session(self, project_root: str) -> LspSession:
        """Return an active LspSession for project_root, restarting if root changed."""
        key = os.path.normcase(os.path.abspath(project_root))
        if (
            self._session is None
            or not self._session.is_alive()
            or self._project_root_key != key
        ):
            if self._session is not None:
                log_err(
                    f"Switching AL LSP workspace from '{self._session.project_root}' "
                    f"to '{project_root}'"
                )
                self._session.shutdown()
                self._session = None
            self._session = LspSession(self.al_lsp_cmd, project_root)
            self._project_root_key = key
        return self._session

    def close(self) -> None:
        """Shut down any active LSP session."""
        with self._lock:
            if self._session is not None:
                self._session.shutdown()
                self._session = None
                self._project_root_key = None

    def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """Dispatch one of the 7 MCP tools to the AL LSP server."""
        if not isinstance(arguments, dict):
            raise ValueError("Tool arguments must be a JSON object")

        with self._lock:
            line_cache: dict[str, list[str]] = {}
            project_arg = arguments.get("projectPath")
            if project_arg is not None and not isinstance(project_arg, str):
                raise ValueError("Parameter 'projectPath' must be a string")

            if name == "al_lsp_workspace_symbols":
                query = require_string(arguments, "query", allow_empty=True)
                root = resolve_project_root(project_path=project_arg)
                session = self._get_session(root)
                # altool launchlspserver only populates workspace symbols once at least
                # one .al document has been opened in the session.
                if not session.opened_files:
                    seed_file = find_first_al_file(root)
                    if seed_file is not None:
                        session.ensure_open(seed_file)
                        time.sleep(0.1)
                raw = session.request("workspace/symbol", {"query": query})
                symbols = []
                for item in raw or []:
                    if not isinstance(item, dict):
                        continue
                    kind_num = int(item.get("kind", 0))
                    loc = item.get("location") or {}
                    loc_uri = loc.get("uri") or ""
                    loc_range = loc.get("range")
                    if loc_range is not None:
                        conv_loc = convert_range_to_location(loc_uri, loc_range, line_cache)
                    else:
                        conv_loc = {
                            "filePath": uri_to_path(loc_uri),
                            "startLine": None,
                            "startCharacter": None,
                            "endLine": None,
                            "endCharacter": None,
                            "preview": "",
                        }
                    symbols.append({
                        "name": item.get("name", ""),
                        "kind": kind_num,
                        "kindName": SYMBOL_KINDS.get(kind_num, f"Kind({kind_num})"),
                        "containerName": item.get("containerName", ""),
                        **conv_loc,
                    })
                return {
                    "projectPath": root,
                    "query": query,
                    "count": len(symbols),
                    "symbols": symbols,
                }

            file_raw = require_string(arguments, "filePath")
            file_path = resolve_file_path(file_raw, project_arg)
            root = resolve_project_root(project_path=project_arg, file_path=file_path)
            session = self._get_session(root)
            uri = session.ensure_open(file_path)

            if name == "al_lsp_document_symbols":
                raw = session.request(
                    "textDocument/documentSymbol",
                    {"textDocument": {"uri": uri}},
                )
                symbols = [
                    _convert_document_symbol(item, str(file_path), line_cache)
                    for item in (raw or [])
                    if isinstance(item, dict)
                ]
                return {
                    "filePath": str(file_path),
                    "count": len(symbols),
                    "symbols": symbols,
                }

            line = require_positive_int(arguments, "line")
            character = require_positive_int(arguments, "character")
            lsp_pos = {"line": line - 1, "character": character - 1}

            if name == "al_lsp_definition":
                raw = session.request(
                    "textDocument/definition",
                    {"textDocument": {"uri": uri}, "position": lsp_pos},
                )
                defs = _convert_location_list(raw, line_cache)
                return {
                    "count": len(defs),
                    "definitions": defs,
                }

            if name == "al_lsp_references":
                include_decl = arguments.get("includeDeclaration", True)
                if not isinstance(include_decl, bool):
                    raise ValueError("Parameter 'includeDeclaration' must be a boolean")
                raw = session.request(
                    "textDocument/references",
                    {
                        "textDocument": {"uri": uri},
                        "position": lsp_pos,
                        "context": {"includeDeclaration": include_decl},
                    },
                )
                refs = _convert_location_list(raw, line_cache)
                # altool launchlspserver can still include the declaration even when
                # context.includeDeclaration is false; filter exact definition match.
                if not include_decl and refs:
                    try:
                        raw_def = session.request(
                            "textDocument/definition",
                            {"textDocument": {"uri": uri}, "position": lsp_pos},
                        )
                        defs = _convert_location_list(raw_def, line_cache)
                        def_keys = {
                            (
                                os.path.normcase(d["filePath"]),
                                d["startLine"],
                                d["startCharacter"],
                                d["endLine"],
                                d["endCharacter"],
                            )
                            for d in defs
                        }
                        if def_keys:
                            refs = [
                                r
                                for r in refs
                                if (
                                    os.path.normcase(r["filePath"]),
                                    r["startLine"],
                                    r["startCharacter"],
                                    r["endLine"],
                                    r["endCharacter"],
                                )
                                not in def_keys
                            ]
                    except Exception:
                        pass
                return {
                    "count": len(refs),
                    "references": refs,
                }

            if name == "al_lsp_hover":
                raw = session.request(
                    "textDocument/hover",
                    {"textDocument": {"uri": uri}, "position": lsp_pos},
                )
                if not isinstance(raw, dict):
                    return {"contents": None, "range": None}
                rng = raw.get("range")
                conv_range = (
                    convert_range_to_location(uri, rng, line_cache)
                    if isinstance(rng, dict)
                    else None
                )
                return {
                    "contents": extract_markup_text(raw.get("contents")),
                    "range": conv_range,
                }

            if name == "al_lsp_signature_help":
                raw = session.request(
                    "textDocument/signatureHelp",
                    {"textDocument": {"uri": uri}, "position": lsp_pos},
                )
                if not isinstance(raw, dict):
                    return {
                        "signatures": [],
                        "activeSignature": None,
                        "activeParameter": None,
                    }
                signatures = []
                for sig in raw.get("signatures") or []:
                    if not isinstance(sig, dict):
                        continue
                    params_out = []
                    for p in sig.get("parameters") or []:
                        if not isinstance(p, dict):
                            continue
                        params_out.append({
                            "label": p.get("label"),
                            "documentation": extract_markup_text(p.get("documentation")),
                        })
                    signatures.append({
                        "label": sig.get("label", ""),
                        "documentation": extract_markup_text(sig.get("documentation")),
                        "parameters": params_out,
                    })
                return {
                    "signatures": signatures,
                    "activeSignature": raw.get("activeSignature"),
                    "activeParameter": raw.get("activeParameter"),
                }

            if name == "al_lsp_rename_preview":
                new_name = require_string(arguments, "newName")
                raw = session.request(
                    "textDocument/rename",
                    {
                        "textDocument": {"uri": uri},
                        "position": lsp_pos,
                        "newName": new_name,
                    },
                    timeout=DEFAULT_RENAME_TIMEOUT,
                )
                return _format_workspace_edit(raw, new_name, line_cache)

            raise KeyError(f"Unknown tool: {name}")


def _format_workspace_edit(
    raw_edit: Any,
    new_name: str,
    line_cache: dict[str, list[str]],
) -> dict[str, Any]:
    """Convert an LSP WorkspaceEdit into a 1-based non-destructive edit preview."""
    edits: list[dict[str, Any]] = []
    resource_ops: list[dict[str, Any]] = []

    if isinstance(raw_edit, dict):
        changes = raw_edit.get("changes")
        if isinstance(changes, dict):
            for edit_uri, text_edits in changes.items():
                for te in text_edits or []:
                    if not isinstance(te, dict) or "range" not in te:
                        continue
                    loc = convert_range_to_location(edit_uri, te["range"], line_cache)
                    loc["newText"] = te.get("newText", "")
                    edits.append(loc)

        doc_changes = raw_edit.get("documentChanges")
        if isinstance(doc_changes, list):
            for entry in doc_changes:
                if not isinstance(entry, dict):
                    continue
                if "kind" in entry:
                    op = dict(entry)
                    for uri_key in ("uri", "oldUri", "newUri"):
                        if uri_key in op:
                            op[uri_key] = uri_to_path(str(op[uri_key]))
                    resource_ops.append(op)
                    continue
                td = entry.get("textDocument") or {}
                edit_uri = td.get("uri") or ""
                for te in entry.get("edits") or []:
                    if not isinstance(te, dict) or "range" not in te:
                        continue
                    loc = convert_range_to_location(edit_uri, te["range"], line_cache)
                    loc["newText"] = te.get("newText", "")
                    edits.append(loc)

    files_affected = sorted({e["filePath"] for e in edits if e.get("filePath")})
    out: dict[str, Any] = {
        "newName": new_name,
        "applied": False,
        "editCount": len(edits),
        "filesAffected": files_affected,
        "edits": edits,
    }
    if resource_ops:
        out["resourceOperations"] = resource_ops
    return out


class McpStdioServer:
    """Newline-delimited JSON-RPC 2.0 MCP stdio server."""

    def __init__(self, manager: LspManager) -> None:
        self.manager = manager

    def _write_message(self, payload: dict[str, Any]) -> None:
        line = (json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8")
        sys.stdout.buffer.write(line)
        sys.stdout.buffer.flush()

    def _send_result(self, req_id: Any, result: Any) -> None:
        self._write_message({
            "jsonrpc": "2.0",
            "id": req_id,
            "result": result,
        })

    def _send_error(self, req_id: Any, code: int, message: str) -> None:
        self._write_message({
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": code, "message": message},
        })

    def run(self) -> int:
        """Read newline-delimited JSON-RPC requests from stdin until EOF."""
        try:
            while True:
                raw_line = sys.stdin.buffer.readline()
                if not raw_line:
                    break
                text = raw_line.decode("utf-8-sig", errors="replace").strip()
                if not text:
                    continue
                try:
                    msg = json.loads(text)
                except json.JSONDecodeError as exc:
                    self._send_error(None, -32700, f"Parse error: {exc}")
                    continue

                if not isinstance(msg, dict):
                    self._send_error(None, -32600, "Invalid Request: expected JSON object")
                    continue

                self._handle_message(msg)
        finally:
            self.manager.close()
        return 0

    def _handle_message(self, msg: dict[str, Any]) -> None:
        method = msg.get("method")
        req_id = msg.get("id")
        has_id = "id" in msg and req_id is not None

        if not isinstance(method, str):
            if has_id:
                self._send_error(req_id, -32600, "Invalid Request: missing method")
            return

        if method in ("notifications/initialized", "initialized", "notifications/cancelled", "$/cancelRequest"):
            return

        if not has_id:
            return

        if method == "initialize":
            self._send_result(
                req_id,
                {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {"tools": {}},
                    "serverInfo": SERVER_INFO,
                },
            )
            return

        if method == "ping":
            self._send_result(req_id, {})
            return

        if method == "tools/list":
            self._send_result(req_id, {"tools": TOOLS})
            return

        if method == "tools/call":
            params = msg.get("params") or {}
            if not isinstance(params, dict):
                self._send_error(req_id, -32602, "Invalid params: expected object")
                return
            tool_name = params.get("name")
            arguments = params.get("arguments")
            if arguments is None:
                arguments = {}
            if not isinstance(tool_name, str):
                self._send_error(req_id, -32602, "Invalid params: missing tool name")
                return
            known = {t["name"] for t in TOOLS}
            if tool_name not in known:
                self._send_error(req_id, -32602, f"Unknown tool: {tool_name}")
                return

            try:
                result = self.manager.call_tool(tool_name, arguments)
                self._send_result(
                    req_id,
                    {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps(result, indent=2, ensure_ascii=False),
                            }
                        ],
                        "isError": False,
                    },
                )
            except Exception as exc:
                self._send_result(
                    req_id,
                    {
                        "content": [
                            {
                                "type": "text",
                                "text": json.dumps({"error": str(exc)}, indent=2, ensure_ascii=False),
                            }
                        ],
                        "isError": True,
                    },
                )
            return

        self._send_error(req_id, -32601, f"Method not found: {method}")


def parse_cli_args_json(raw_arg: str) -> dict[str, Any]:
    """Parse JSON arguments from an inline JSON string or a JSON file path."""
    trimmed = raw_arg.strip()
    if trimmed.startswith("@"):
        file_text = read_text_utf8(Path(trimmed[1:]))
        parsed = json.loads(file_text)
    elif trimmed.startswith("{"):
        parsed = json.loads(trimmed)
    elif os.path.isfile(raw_arg):
        file_text = read_text_utf8(Path(raw_arg))
        parsed = json.loads(file_text)
    else:
        parsed = json.loads(trimmed)

    if not isinstance(parsed, dict):
        raise ValueError("CLI JSON arguments must decode to a JSON object")
    return parsed


def run_cli(manager: LspManager, argv: list[str]) -> int:
    """Execute `--cli <tool_name> [<json_args_string_or_file>]` once and exit."""
    if len(argv) < 3 or len(argv) > 4:
        log_err("Usage: al-lsp-mcp.py --cli <tool_name> <json_args_string_or_file>")
        return 1

    tool_name = argv[2]
    known = {t["name"] for t in TOOLS}
    if tool_name not in known:
        log_err(f"Unknown tool '{tool_name}'. Available: {', '.join(sorted(known))}")
        return 1

    raw_json = argv[3] if len(argv) == 4 else "{}"
    try:
        args = parse_cli_args_json(raw_json)
        result = manager.call_tool(tool_name, args)
    except Exception as exc:
        log_err(f"Error: {exc}")
        return 1
    finally:
        manager.close()

    output = (json.dumps(result, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    sys.stdout.buffer.write(output)
    sys.stdout.buffer.flush()
    return 0


def main() -> int:
    al_lsp_cmd = os.path.abspath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "al-lsp.cmd")
    )
    manager = LspManager(al_lsp_cmd)

    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        return run_cli(manager, sys.argv)

    if len(sys.argv) > 1:
        log_err(f"Unexpected arguments: {sys.argv[1:]}. Use no arguments for MCP stdio or --cli.")
        return 1

    server = McpStdioServer(manager)
    return server.run()


if __name__ == "__main__":
    sys.exit(main())
