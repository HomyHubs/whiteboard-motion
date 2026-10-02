from __future__ import annotations
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import argparse, json, re, time
from pathlib import Path
from urllib.parse import urlparse
from .hardware import detect_nvidia_gpus, hardware_report
from .profiles import select_qwen_profile
from .models import ModelManager
from .projects import ProjectStore,InvalidProjectId
from .voices import VoiceProfileStore
from .security.audit import get_voice_audit_log
from .jobs import JobManager
from .services import submit_model_download
from .media import media_report
from .updates import check_for_update
from . import __version__

_MEDIA: dict | None = None
def cached_media_report(refresh: bool = False) -> dict:
    global _MEDIA
    if _MEDIA is None or refresh: _MEDIA = media_report()
    return _MEDIA

JOBS = JobManager()
MODELS = ModelManager()
PROJECTS = ProjectStore()
VOICES = VoiceProfileStore()
ROOT = Path(__file__).resolve().parent.parent

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
        self.send_header("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS")
        self.end_headers(); self.wfile.write(body)
    def _raw(self,status:int,body:bytes,content_type:str)->None:
        self.send_response(status);self.send_header("Content-Type",content_type);self.send_header("Content-Length",str(len(body)));self.send_header("Access-Control-Allow-Origin","http://localhost:1420");self.end_headers();self.wfile.write(body)
    def _body(self) -> dict:
        size = int(self.headers.get("Content-Length", "0")); raw = self.rfile.read(size) if size else b"{}"
        try: return json.loads(raw or b"{}")
        except json.JSONDecodeError: return {}
    def do_OPTIONS(self): self._json(204, {})
    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/health": return self._json(200, {"ok": True, "version": __version__})
        if path == "/updates": return self._json(200, check_for_update())
        if path == "/preview": return self._raw(200,(ROOT/'assets'/'preview.html').read_bytes(),'text/html; charset=utf-8')
        if path == "/projects": return self._json(200,PROJECTS.list())
        project_match=re.fullmatch(r"/projects/([a-z0-9-]+)",path)
        if project_match:
            try:return self._json(200,PROJECTS.get(project_match.group(1)))
            except (KeyError,InvalidProjectId) as exc:return self._json(404,{"error":str(exc)})
        scenes_match=re.fullmatch(r"/projects/([a-z0-9-]+)/scenes",path)
        if scenes_match:
            try:return self._json(200,PROJECTS.list_scenes(scenes_match.group(1)))
            except (KeyError,InvalidProjectId) as exc:return self._json(404,{"error":str(exc)})
        scene_match=re.fullmatch(r"/projects/([a-z0-9-]+)/scenes/([a-z0-9-]+)",path)
        if scene_match:
            try:return self._json(200,PROJECTS.load_scene(*scene_match.groups()))
            except (KeyError,InvalidProjectId) as exc:return self._json(404,{"error":str(exc)})
        if path == "/voices": return self._json(200, VOICES.list())
        voice_match = re.fullmatch(r"/voices/([a-z0-9-]+)", path)
        if voice_match:
            try: return self._json(200, VOICES.get(voice_match.group(1)))
            except (KeyError, ValueError) as exc: return self._json(404, {"error": str(exc)})
        if path == "/audit/voice-clones":
            from urllib.parse import parse_qs
            qs = parse_qs(urlparse(self.path).query)
            limit = int(qs.get("limit", [50])[0])
            return self._json(200, get_voice_audit_log(limit=limit))
        if path == "/hardware": return self._json(200, hardware_report())
        if path == "/profile":
            gpus = detect_nvidia_gpus(); return self._json(200, select_qwen_profile(gpus[0] if gpus else None).to_dict())
        if path == "/media": return self._json(200, cached_media_report("refresh=1" in urlparse(self.path).query))
        if path == "/models": return self._json(200, MODELS.list_status())
        if path == "/jobs": return self._json(200, [job.to_dict() for job in JOBS.list()])
        match = re.fullmatch(r"/jobs/([a-f0-9]+)", path)
        if match:
            job = JOBS.get(match.group(1)); return self._json(200, job.to_dict()) if job else self._json(404, {"error": "not found"})
        self._json(404, {"error": "not found"})
    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/projects":
            body=self._body()
            try:return self._json(201,PROJECTS.create(str(body.get('name','')),str(body.get('aspectRatio','16:9'))))
            except ValueError as exc:return self._json(400,{'error':str(exc)})
        if path == "/voices":
            body = self._body()
            try:
                created = VOICES.create(
                    voice_id=str(body.get("id", "")),
                    name=str(body.get("name", "")),
                    language=str(body.get("language", "vi")),
                    is_clone=bool(body.get("isClone", False)),
                    reference_audio=Path(body["referenceAudio"]) if body.get("referenceAudio") else None,
                    reference_text=str(body.get("referenceText", "")),
                    consent_confirmed=bool(body.get("consentConfirmed", False)),
                    consent_statement=str(body.get("consentStatement", "")),
                )
                return self._json(201, created)
            except (ValueError, FileNotFoundError, PermissionError) as exc:
                return self._json(400, {"error": str(exc)})
        model_match=re.fullmatch(r"/models/([A-Za-z0-9._-]+)/(accept|download|verify)",path)
        if model_match:
            model_id,action=model_match.groups()
            try:
                if action=='accept': MODELS.accept_license(model_id);return self._json(200,next(x for x in MODELS.list_status() if x['id']==model_id))
                if action=='download':
                    job=submit_model_download(MODELS,JOBS,model_id);return self._json(202,job.to_dict())
                if action=='verify':return self._json(200,MODELS.verify(model_id))
            except (KeyError,RuntimeError) as exc:return self._json(400,{'error':str(exc)})
        if path == "/jobs/demo":
            body = self._body(); uses_gpu = bool(body.get("usesGpu", False)); seconds = min(60.0, max(0.1, float(body.get("seconds", 5))))
            job = JOBS.submit("demo-gpu" if uses_gpu else "demo-cpu", demo_job(seconds, uses_gpu), uses_gpu)
            return self._json(202, job.to_dict())
        match = re.fullmatch(r"/jobs/([a-f0-9]+)/cancel", path)
        if match: return self._json(200, {"cancelled": JOBS.cancel(match.group(1))})
        self._json(404, {"error": "not found"})
    def do_PUT(self):
        path=urlparse(self.path).path;match=re.fullmatch(r"/projects/([a-z0-9-]+)/scenes/([a-z0-9-]+)",path)
        if not match:return self._json(404,{"error":"not found"})
        try:return self._json(200,PROJECTS.save_scene(*match.groups(),self._body()))
        except (KeyError,ValueError,InvalidProjectId,json.JSONDecodeError) as exc:return self._json(400,{"error":str(exc)})
    def do_DELETE(self):
        path=urlparse(self.path).path
        voice_match = re.fullmatch(r"/voices/([a-z0-9-]+)", path)
        if voice_match:
            try:
                VOICES.delete(voice_match.group(1))
                return self._json(200, {"deleted": True, "id": voice_match.group(1)})
            except (KeyError, ValueError) as exc:
                return self._json(400, {"error": str(exc)})
        match=re.fullmatch(r"/models/([A-Za-z0-9._-]+)",path)
        if not match:return self._json(404,{"error":"not found"})
        try:MODELS.entry(match.group(1));MODELS.remove(match.group(1));return self._json(200,{"removed":True,"id":match.group(1)})
        except KeyError as exc:return self._json(404,{"error":str(exc)})


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--host", default="127.0.0.1"); parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args(argv); server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"BACKEND=http://{args.host}:{args.port}", flush=True)
    try: server.serve_forever()
    except KeyboardInterrupt: pass
    finally: JOBS.shutdown(False); server.server_close()
    return 0
if __name__ == "__main__": raise SystemExit(main())
