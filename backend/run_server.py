"""
Entry point for the local BIM Agentic Bridge backend.

Usage:
  python run_server.py
  python run_server.py --configure --provider gemini --key YOUR_KEY
  python run_server.py --stop
  BimAgenticBridge.Backend.exe   (frozen)
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import signal
import sys
import time
from pathlib import Path


def _prepare_sys_path() -> None:
    here = Path(__file__).resolve().parent
    if str(here) not in sys.path:
        sys.path.insert(0, str(here))


def _configure_logging() -> Path:
    from app.paths import backend_log_path, ensure_local_app_data

    ensure_local_app_data()
    log_path = backend_log_path()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    return log_path


def _write_pid(pid: int) -> None:
    from app.paths import backend_pid_path, ensure_local_app_data

    ensure_local_app_data()
    backend_pid_path().write_text(
        json.dumps({"pid": pid, "started_at": time.time()}) + "\n",
        encoding="utf-8",
    )


def _read_pid() -> int | None:
    from app.paths import backend_pid_path

    path = backend_pid_path()
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return int(data.get("pid"))
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return None


def _clear_pid() -> None:
    from app.paths import backend_pid_path

    path = backend_pid_path()
    if path.is_file():
        try:
            path.unlink()
        except OSError:
            pass


def cmd_configure(args: argparse.Namespace) -> int:
    from app.credentials import Credentials, save_credentials
    from app.paths import credentials_dat_path, ensure_local_app_data
    from app.runtime_config import ensure_runtime_config

    ensure_local_app_data()
    ensure_runtime_config()

    provider = (args.provider or "gemini").strip().lower()
    key = (args.key or "").strip()
    if not key:
        print("ERROR: --key is required.", file=sys.stderr)
        return 2

    creds = Credentials(
        llm_provider=provider,
        gemini_api_key=key if provider != "openai" else "",
        openai_api_key=key if provider == "openai" else "",
        gemini_model=args.gemini_model or "gemini-1.5-flash",
        openai_model=args.openai_model or "gpt-4o-mini",
    )
    path = save_credentials(creds)
    print(f"Saved encrypted credentials to: {path}")
    print(f"(Never commit or share {credentials_dat_path().name}.)")
    return 0


def cmd_stop(_: argparse.Namespace) -> int:
    import urllib.error
    import urllib.request

    from app.paths import PRODUCT_NAME
    from app.runtime_config import load_runtime_config

    cfg = load_runtime_config()
    pid = _read_pid()

    # Prefer graceful identity check: only stop if /health is our product.
    url = f"http://{cfg.api_host}:{cfg.api_port}/health"
    is_ours = False
    try:
        with urllib.request.urlopen(url, timeout=2) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            is_ours = body.get("product") == PRODUCT_NAME
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        is_ours = False

    if not is_ours and pid is None:
        print("No BIM Agentic Bridge backend appears to be running.")
        _clear_pid()
        return 0

    if not is_ours and pid is not None:
        # Stale PID or crashed process — try kill by PID only if process name matches later.
        print(f"Health check did not identify our product; attempting PID {pid} stop if alive.")

    target_pid = pid
    if target_pid is None:
        print("Backend is healthy but PID file is missing; refuse to kill unknown process.")
        print("Stop it manually from Task Manager if needed.")
        return 1

    try:
        if sys.platform == "win32":
            import ctypes

            PROCESS_TERMINATE = 0x0001
            handle = ctypes.windll.kernel32.OpenProcess(PROCESS_TERMINATE, False, target_pid)
            if not handle:
                print(f"Process {target_pid} is not running (stale PID).")
                _clear_pid()
                return 0
            ctypes.windll.kernel32.TerminateProcess(handle, 1)
            ctypes.windll.kernel32.CloseHandle(handle)
        else:
            os.kill(target_pid, signal.SIGTERM)
        print(f"Stopped backend process {target_pid}.")
        _clear_pid()
        return 0
    except OSError as exc:
        print(f"Failed to stop PID {target_pid}: {exc}", file=sys.stderr)
        return 1


def cmd_serve(_: argparse.Namespace) -> int:
    log_path = _configure_logging()
    logger = logging.getLogger("bimagenticbridge")

    from app.config import bootstrap_settings_from_runtime, clear_settings_cache, get_settings
    from app.paths import PRODUCT_NAME
    from app.runtime_config import ensure_runtime_config

    bootstrap_settings_from_runtime()
    clear_settings_cache()
    cfg = ensure_runtime_config()
    settings = get_settings()

    host = settings.api_host if settings.api_host in ("127.0.0.1", "localhost") else "127.0.0.1"
    port = int(settings.api_port or cfg.api_port or 8000)

    if host not in ("127.0.0.1", "localhost"):
        logger.error("Refusing to bind to non-loopback host %s", host)
        return 2

    _write_pid(os.getpid())
    logger.info("%s backend starting on http://%s:%s (log: %s)", PRODUCT_NAME, host, port, log_path)

    import uvicorn

    try:
        uvicorn.run(
            "app.main:app",
            host=host,
            port=port,
            log_level="info",
            factory=False,
        )
    finally:
        _clear_pid()
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="BIM Agentic Bridge local backend")
    sub = parser.add_subparsers(dest="command")

    # Default serve when no subcommand — also support flags at top level.
    parser.add_argument("--stop", action="store_true", help="Stop the running local backend")
    parser.add_argument(
        "--configure",
        action="store_true",
        help="Save DPAPI-protected API credentials",
    )
    parser.add_argument("--provider", default="gemini", help="gemini or openai")
    parser.add_argument("--key", default="", help="API key value")
    parser.add_argument("--gemini-model", default="gemini-1.5-flash")
    parser.add_argument("--openai-model", default="gpt-4o-mini")

    serve_p = sub.add_parser("serve", help="Run the FastAPI server (default)")
    serve_p.set_defaults(func=cmd_serve)

    stop_p = sub.add_parser("stop", help="Stop the local backend")
    stop_p.set_defaults(func=cmd_stop)

    cfg_p = sub.add_parser("configure", help="Save encrypted API credentials")
    cfg_p.add_argument("--provider", default="gemini")
    cfg_p.add_argument("--key", required=True)
    cfg_p.add_argument("--gemini-model", default="gemini-1.5-flash")
    cfg_p.add_argument("--openai-model", default="gpt-4o-mini")
    cfg_p.set_defaults(func=cmd_configure)

    return parser


def main(argv: list[str] | None = None) -> int:
    _prepare_sys_path()
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command:
        return int(args.func(args))
    if args.stop:
        return cmd_stop(args)
    if args.configure:
        return cmd_configure(args)
    return cmd_serve(args)


if __name__ == "__main__":
    raise SystemExit(main())
