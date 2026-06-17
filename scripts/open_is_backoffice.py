"""
Quick launcher for IS-BACKOFFICE Streamlit app.

Usage examples:
  python scripts/open_is_backoffice.py                # start app on default port and open command center
  python scripts/open_is_backoffice.py --port 8503 --page plant_simulator
  python scripts/open_is_backoffice.py --page is-backoffice-command-center

This script will:
 - check whether the chosen port is already in use
 - if not, start `streamlit run streamlit_app.py --server.port <port>` using the current Python
 - wait until the app responds, then open the requested page in the default browser

Works on Windows/macOS/Linux with a standard Python 3 environment.
"""

from __future__ import annotations

import argparse
import os
import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path
from typing import Optional

try:
    # Python 3
    from urllib.request import urlopen
    from urllib.error import URLError
except Exception:
    urlopen = None  # type: ignore
    URLError = Exception


def is_port_in_use(port: int, host: str = "127.0.0.1") -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.settimeout(0.5)
        res = s.connect_ex((host, port))
        return res == 0
    finally:
        try:
            s.close()
        except Exception:
            pass


def wait_for_root(port: int, timeout: float = 30.0) -> bool:
    url = f"http://localhost:{port}/"
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if urlopen is None:
                time.sleep(0.5)
                continue
            resp = urlopen(url, timeout=2)
            code = getattr(resp, "status", None) or getattr(resp, "getcode", lambda: None)()
            if code and int(code) < 400:
                return True
        except URLError:
            pass
        except Exception:
            pass
        time.sleep(0.5)
    return False


def start_streamlit(python_exe: str, app_script: str, port: int, cwd: Optional[str] = None) -> subprocess.Popen:
    cmd = [python_exe, "-m", "streamlit", "run", app_script, "--server.port", str(port)]
    print("Starting Streamlit:", " ".join(cmd))
    kwargs = {"cwd": cwd or os.getcwd(), "stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL}
    if os.name == "nt":
        # Detach on Windows so it keeps running after this script exits
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        # start a new session on POSIX
        kwargs["start_new_session"] = True
    p = subprocess.Popen(cmd, **kwargs)
    return p


def normalize_page(page: str) -> str:
    if not page:
        return ""
    key = page.strip().lower()
    mapping = {
        "is-backoffice-command-center": "command_center",
        "is-backoffice-commandcenter": "command_center",
        "is-backoffice": "",
        "command-center": "command_center",
        "commandcenter": "command_center",
        "command_center": "command_center",
    }
    return mapping.get(key, key)


def open_page_in_browser(port: int, page: str) -> str:
    if page:
        url = f"http://localhost:{port}/{page}"
    else:
        url = f"http://localhost:{port}/"
    print("Opening URL:", url)
    webbrowser.open(url)
    return url


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Open IS-BACKOFFICE and a specific menu/page quickly.")
    parser.add_argument("--port", "-p", type=int, default=8503, help="Port to run/connect to (default: 8503)")
    parser.add_argument("--page", type=str, default="command_center", help="Page to open (e.g. command_center, plant_simulator). Accepts 'is-backoffice-command-center'.")
    parser.add_argument("--python", type=str, default=sys.executable, help="Python executable to use to start Streamlit (default: current Python)")
    parser.add_argument("--cwd", type=str, default=None, help="Working directory (project root). If omitted, the script assumes repository root one level up from this file.")
    parser.add_argument("--wait", type=float, default=30.0, help="Seconds to wait for the app to start (default: 30)")
    parser.add_argument("--no-start", action="store_true", help="Do not start Streamlit if the port is free; only open browser if server already running")
    args = parser.parse_args(argv)

    page = normalize_page(args.page)

    # Resolve working directory and app script
    script_path = Path(__file__).resolve()
    repo_root = Path(args.cwd) if args.cwd else script_path.parent.parent
    app_script = repo_root / "streamlit_app.py"
    if not app_script.exists():
        print(f"Error: cannot find {app_script}. Run this script from the repository or pass --cwd.")
        return 2

    port_in_use = is_port_in_use(args.port)

    proc = None
    if not port_in_use:
        if args.no_start:
            print(f"Port {args.port} is free and --no-start was specified. Not starting Streamlit.")
        else:
            proc = start_streamlit(args.python, str(app_script), args.port, cwd=str(repo_root))
    else:
        print(f"Port {args.port} appears to be in use — assuming IS-BACKOFFICE is already running.")

    # Wait for root to be available before opening target page
    ok = wait_for_root(args.port, timeout=args.wait)
    if not ok:
        print(f"Timed out after {args.wait}s waiting for http://localhost:{args.port}/ to respond.")
        if not port_in_use and proc is None:
            return 3

    open_page_in_browser(args.port, page)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
