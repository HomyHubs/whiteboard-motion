from __future__ import annotations
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import argparse, json, re, time
from urllib.parse import urlparse
from .hardware import detect_nvidia_gpus, hardware_report
from .profiles import select_qwen_profile
from .models import ModelManager
from .jobs import JobManager

JOBS = JobManager()
MODELS = ModelManager()

def demo_job(seconds: float, use_gpu: bool):
    def run(ctx):
        steps = max(1, int(seconds * 10))
        for index in range(steps):
            ctx.check_cancelled(); time.sleep(seconds / steps)
            ctx.report((index + 1) / steps, f"Bước {index + 1}/{steps}")
        return {"ok": True, "usesGpu": use_gpu}
    return run

class Handler(BaseHTTPRequestHandler):
    server_version = "WhiteboardBackend/0.1"
    def log_message(self, fmt, *args): return
    def _json(self, status: int, data) -> None:
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "http://localhost:1420")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.end_headers(); self.wfile.write(body)
    def _body(self) -> dict:
        size = int(self.headers.get("Content-Length", "0")); raw = self.rfile.read(size) if size else b"{}"
        return json.loads(raw or b"{}")
    def do_OPTIONS(self): self._json(204, {})
    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/health": return self._json(200, {"ok": True})
        if path == "/hardware": return self._json(200, hardware_report())
        if path == "/profile":
            gpus = detect_nvidia_gpus(); return self._json(200, select_qwen_profile(gpus[0] if gpus else None).to_dict())
        if path == "/models": return self._json(200, MODELS.list_status())
        if path == "/jobs": return self._json(200, [job.to_dict() for job in JOBS.list()])
        match = re.fullmatch(r"/jobs/([a-f0-9]+)", path)
        if match:
            job = JOBS.get(match.group(1)); return self._json(200, job.to_dict()) if job else self._json(404, {"error": "not found"})
        self._json(404, {"error": "not found"})
    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/jobs/demo":
            body = self._body(); uses_gpu = bool(body.get("usesGpu", False)); seconds = min(60.0, max(0.1, float(body.get("seconds", 5))))
            job = JOBS.submit("demo-gpu" if uses_gpu else "demo-cpu", demo_job(seconds, uses_gpu), uses_gpu)
            return self._json(202, job.to_dict())
        match = re.fullmatch(r"/jobs/([a-f0-9]+)/cancel", path)
        if match: return self._json(200, {"cancelled": JOBS.cancel(match.group(1))})
        self._json(404, {"error": "not found"})

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--host", default="127.0.0.1"); parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv); server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"BACKEND=http://{args.host}:{args.port}", flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: JOBS.shutdown(False); server.server_close()
    return 0
if __name__ == "__main__": raise SystemExit(main())
