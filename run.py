#!/usr/bin/env python3
"""
SIF Sentinel — Universal Single-Command Runner
Supports Windows, macOS, and Linux.

Performs:
1. System pre-flight checks (Python >= 3.10, Node.js, npm).
2. Stale port cleanup (ensures ports 8000 & 5173 are free).
3. Backend Python requirements verification & auto-installation via pip.
4. Frontend dependencies verification & auto-installation via npm.
5. Concurrent launch of FastAPI backend and Vite React frontend.
6. Health polling on both services until ready.
7. Automatic browser launch to http://localhost:5173/login.
8. Instant, clean shutdown of both servers on Ctrl+C (Windows/Linux) or Cmd+C (macOS).
"""

import os
import sys
import time
import atexit
import shutil
import signal
import platform
import subprocess
import urllib.request
import urllib.error
import webbrowser
from pathlib import Path

# Paths
ROOT_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = ROOT_DIR / "frontend"
REQUIREMENTS_FILE = ROOT_DIR / "requirements.txt"

BACKEND_URL = "http://127.0.0.1:8000"
BACKEND_HEALTH = f"{BACKEND_URL}/api/v1/health"
FRONTEND_URL = "http://localhost:5173"
LOGIN_URL = f"{FRONTEND_URL}/login"

IS_WINDOWS = platform.system() == "Windows"

# Global references for cleanup
active_processes = []
is_cleaning_up = False


def print_banner(text: str) -> None:
    border = "=" * 65
    print(f"\n{border}")
    print(f"  {text}")
    print(f"{border}\n")


def free_port_if_in_use(port: int) -> None:
    """Detect and terminate any stale processes occupying the target port."""
    if IS_WINDOWS:
        try:
            cmd = f'netstat -ano | findstr :{port}'
            out = subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL)
            for line in out.strip().splitlines():
                parts = line.split()
                if len(parts) >= 5 and f":{port}" in parts[1] and parts[3] == "LISTENING":
                    pid = parts[4]
                    if pid != "0" and int(pid) != os.getpid():
                        print(f"[*] Port {port} is held by stale PID {pid}. Terminating...")
                        subprocess.run(["taskkill", "/F", "/PID", pid], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass
    else:
        try:
            subprocess.run(["fuser", "-k", f"{port}/tcp"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass


def check_prerequisites() -> None:
    """Verify minimum required runtime tools."""
    if sys.version_info < (3, 10):
        print(f"[ERROR] Python 3.10+ required. Detected Python {sys.version.split()[0]}")
        sys.exit(1)

    node_cmd = shutil.which("node")
    if not node_cmd:
        print("[ERROR] Node.js is not found in PATH.")
        print("Please install Node.js (v18 or higher) from https://nodejs.org/")
        sys.exit(1)

    npm_cmd = shutil.which("npm") or shutil.which("npm.cmd")
    if not npm_cmd:
        print("[ERROR] npm is not found in PATH.")
        print("Please ensure npm is installed alongside Node.js.")
        sys.exit(1)


def check_and_install_python_deps() -> None:
    """Check required Python packages; install from requirements.txt if missing."""
    required_modules = [
        ("fastapi", "fastapi"),
        ("uvicorn", "uvicorn"),
        ("sqlalchemy", "sqlalchemy"),
        ("pydantic", "pydantic"),
        ("sklearn", "scikit-learn"),
        ("joblib", "joblib"),
        ("numpy", "numpy"),
        ("pandas", "pandas"),
        ("jwt", "pyjwt"),
        ("bcrypt", "bcrypt"),
        ("email_validator", "email-validator"),
    ]

    missing = []
    for mod_name, pkg_name in required_modules:
        try:
            __import__(mod_name)
        except ImportError:
            missing.append(pkg_name)

    if missing:
        print(f"[1/4] Missing Python dependencies: {', '.join(missing)}")
        print(f"      Installing requirements from {REQUIREMENTS_FILE} ...")
        cmd = [sys.executable, "-m", "pip", "install", "-r", str(REQUIREMENTS_FILE)]
        result = subprocess.run(cmd, cwd=str(ROOT_DIR))
        if result.returncode != 0:
            print("\n[ERROR] Failed to install Python dependencies.")
            sys.exit(result.returncode)
        print("      Python dependencies installed successfully.")
    else:
        print("[1/4] Python dependencies already satisfied.")


def check_and_install_frontend_deps() -> None:
    """Check frontend/node_modules; run npm install if missing."""
    node_modules = FRONTEND_DIR / "node_modules"
    npm_cmd = shutil.which("npm.cmd") if IS_WINDOWS else shutil.which("npm") or "npm"

    if not node_modules.exists() or not (node_modules / "vite").exists():
        print(f"[2/4] Frontend node_modules not found in {FRONTEND_DIR}.")
        print("      Installing frontend dependencies (npm install)...")
        result = subprocess.run([npm_cmd, "install"], cwd=str(FRONTEND_DIR), shell=False)
        if result.returncode != 0:
            print("\n[ERROR] Failed to run 'npm install' in frontend directory.")
            sys.exit(result.returncode)
        print("      Frontend dependencies installed successfully.")
    else:
        print("[2/4] Frontend dependencies already satisfied.")


def wait_for_service(url: str, name: str, timeout_seconds: int = 30) -> bool:
    """Poll a service URL until it returns HTTP 200 or timeout is reached."""
    start_time = time.time()
    while time.time() - start_time < timeout_seconds:
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "SIF-Sentinel-Runner/1.0"}
            )
            with urllib.request.urlopen(req, timeout=2) as response:
                if response.status in (200, 304):
                    return True
        except Exception:
            time.sleep(0.5)
    return False


def terminate_process(proc: subprocess.Popen, name: str) -> None:
    """Cleanly and forcefully terminate a subprocess and all its children."""
    if proc is None or proc.poll() is not None:
        return

    try:
        if IS_WINDOWS:
            # Forcefully kill process tree (/F /T) to terminate child node/uvicorn workers
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        else:
            try:
                pgid = os.getpgid(proc.pid)
                os.killpg(pgid, signal.SIGTERM)
            except Exception:
                proc.terminate()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                try:
                    pgid = os.getpgid(proc.pid)
                    os.killpg(pgid, signal.SIGKILL)
                except Exception:
                    proc.kill()
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass
    print(f"[*] Terminated {name} (PID: {proc.pid})")


def cleanup_all(signum=None, frame=None) -> None:
    """Graceful, guaranteed shutdown of all running servers."""
    global is_cleaning_up
    if is_cleaning_up:
        return
    is_cleaning_up = True

    print("\n\n===================================================================")
    print("  Stopping SIF Sentinel servers (Ctrl+C / exit received)...")
    print("===================================================================")

    for proc, name in active_processes:
        terminate_process(proc, name)

    # Double check ports 8000 and 5173
    free_port_if_in_use(8000)
    free_port_if_in_use(5173)

    print("[*] All servers stopped cleanly. Ports released.")
    print("===================================================================\n")
    sys.exit(0)


def main() -> None:
    global active_processes

    os.chdir(str(ROOT_DIR))
    print_banner("SIF Sentinel — AI Safety Intelligence Launcher")

    print("[*] Checking system prerequisites...")
    check_prerequisites()

    print("[*] Ensuring ports 8000 and 5173 are free...")
    free_port_if_in_use(8000)
    free_port_if_in_use(5173)

    print("[*] Verifying dependencies...")
    check_and_install_python_deps()
    check_and_install_frontend_deps()

    # Register exit handlers for all termination scenarios
    atexit.register(cleanup_all)
    signal.signal(signal.SIGINT, cleanup_all)
    signal.signal(signal.SIGTERM, cleanup_all)
    if hasattr(signal, "SIGBREAK"):  # Windows Ctrl+Break
        signal.signal(signal.SIGBREAK, cleanup_all)

    print("\n[3/4] Starting FastAPI backend and React frontend...")

    # Start FastAPI Backend
    backend_cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "backend.app.main:app",
        "--host",
        "127.0.0.1",
        "--port",
        "8000",
    ]

    backend_proc = subprocess.Popen(
        backend_cmd,
        cwd=str(ROOT_DIR),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        preexec_fn=os.setsid if not IS_WINDOWS else None,
    )

    # Start Vite Frontend
    npm_cmd = shutil.which("npm.cmd") if IS_WINDOWS else shutil.which("npm") or "npm"
    frontend_proc = subprocess.Popen(
        [npm_cmd, "run", "dev"],
        cwd=str(FRONTEND_DIR),
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        shell=False,
        preexec_fn=os.setsid if not IS_WINDOWS else None,
    )

    active_processes = [
        (backend_proc, "FastAPI Backend"),
        (frontend_proc, "React Frontend (Vite)"),
    ]

    print("[4/4] Waiting for services to respond...")
    backend_ready = wait_for_service(BACKEND_HEALTH, "FastAPI Backend", timeout_seconds=25)
    if not backend_ready:
        print("[ERROR] FastAPI backend failed to respond on port 8000 within 25 seconds.")
        cleanup_all()

    frontend_ready = wait_for_service(FRONTEND_URL, "Vite Frontend", timeout_seconds=25)
    if not frontend_ready:
        print("[ERROR] React frontend failed to respond on port 5173 within 25 seconds.")
        cleanup_all()

    # Success Banner
    print("\n" + "=" * 65)
    print("  SUCCESS: SIF Sentinel is up and running!")
    print("=" * 65)
    print(f"  * Backend API:        {BACKEND_URL}")
    print(f"  * API Docs (Swagger): {BACKEND_URL}/docs")
    print(f"  * Frontend App:       {FRONTEND_URL}")
    print(f"  * Login / Register:   {LOGIN_URL}")
    print("=" * 65)
    print(f"  Opening default browser to {LOGIN_URL} ...")
    print("  Press Ctrl+C (or Cmd+C on macOS) at any time to stop all servers.")
    print("=" * 65 + "\n")

    try:
        webbrowser.open(LOGIN_URL)
    except Exception as e:
        print(f"[*] Could not open browser automatically: {e}")
        print(f"    Please navigate to {LOGIN_URL}")

    # Keep running and monitor process health
    try:
        while True:
            for proc, name in active_processes:
                code = proc.poll()
                if code is not None:
                    print(f"\n[WARNING] {name} exited unexpectedly with code {code}.")
                    cleanup_all()
            time.sleep(1)
    except KeyboardInterrupt:
        cleanup_all()


if __name__ == "__main__":
    main()
