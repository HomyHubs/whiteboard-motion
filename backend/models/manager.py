from __future__ import annotations
import hashlib, json, os, shutil, urllib.request, zipfile
from pathlib import Path
from ..config import models_dir

class LicenseNotAccepted(RuntimeError): pass

class ModelManager:
    def __init__(self, root: Path | None = None, manifest: Path | None = None):
        self.root = root or models_dir(); self.manifest_path = manifest or Path(__file__).with_name("manifest.json")
        self.root.mkdir(parents=True, exist_ok=True)
    def entries(self) -> list[dict]: return json.loads(self.manifest_path.read_text(encoding="utf-8"))["models"]
    def entry(self, model_id: str) -> dict:
        for item in self.entries():
            if item["id"] == model_id: return item
        raise KeyError(f"Unknown model: {model_id}")
    def path(self, model_id: str) -> Path: return self.root / model_id
    def marker(self, model_id: str) -> Path: return self.path(model_id) / ".whiteboard-model.json"
    def acceptance_marker(self, model_id: str) -> Path: return self.root / ".licenses" / f"{model_id}.json"
    def is_installed(self, model_id: str) -> bool: return self.marker(model_id).exists()
    def is_license_accepted(self, model_id: str) -> bool:
        item=self.entry(model_id)
        if not item.get("requires_acceptance"): return True
        marker=self.acceptance_marker(model_id)
        if not marker.exists(): return False
        try: accepted=json.loads(marker.read_text(encoding="utf-8"))
        except (OSError,json.JSONDecodeError): return False
        return accepted.get("revision")==item.get("revision") and accepted.get("license")==item.get("license")
    def accept_license(self, model_id: str, accepted_by: str = "local-user") -> Path:
        item=self.entry(model_id); path=self.acceptance_marker(model_id); path.parent.mkdir(parents=True,exist_ok=True)
        path.write_text(json.dumps({"id":model_id,"revision":item["revision"],"license":item["license"],"license_url":item.get("license_url"),"accepted_by":accepted_by},ensure_ascii=False,indent=2),encoding="utf-8")
        return path
    def list_status(self) -> list[dict]:
        return [{**item,"installed":self.is_installed(item["id"]),"license_accepted":self.is_license_accepted(item["id"]),"path":str(self.path(item["id"]))} for item in self.entries()]
    def _require_license(self,item:dict)->None:
        if item.get("requires_acceptance") and not self.is_license_accepted(item["id"]):
            raise LicenseNotAccepted(f"Chưa chấp nhận license cho {item['id']}. Chạy: models accept {item['id']}")
    def download(self, model_id: str) -> Path:
        item=self.entry(model_id); self._require_license(item); target=self.path(model_id); target.mkdir(parents=True,exist_ok=True)
        if item["source"]=="huggingface": self._download_hf(item,target)
        elif item["source"]=="archive": self._download_archive(item,target)
        else: raise RuntimeError(f"Unsupported source: {item['source']}")
        self.marker(model_id).write_text(json.dumps(item,ensure_ascii=False,indent=2),encoding="utf-8")
        return target
    def _download_hf(self,item:dict,target:Path)->None:
        try: from huggingface_hub import snapshot_download
        except ImportError as exc: raise RuntimeError("Cài huggingface-hub trước khi download model") from exc
        kwargs={"repo_id":item["repo_id"],"revision":item["revision"],"local_dir":target}
        if item.get("allow_patterns"): kwargs["allow_patterns"]=item["allow_patterns"]
        snapshot_download(**kwargs)
    def _download_archive(self,item:dict,target:Path)->None:
        archive=target.parent/f".{item['id']}-{item['revision']}.zip.part"
        start=archive.stat().st_size if archive.exists() else 0
        req=urllib.request.Request(item["url"],headers={"User-Agent":"whiteboard-video/0.2"})
        if start: req.add_header("Range",f"bytes={start}-")
        with urllib.request.urlopen(req,timeout=120) as response:
            append=start and getattr(response,"status",200)==206
            with open(archive,"ab" if append else "wb") as f: shutil.copyfileobj(response,f,1024*1024)
        digest=hashlib.sha256(archive.read_bytes()).hexdigest()
        if digest.lower()!=item["sha256"].lower(): raise RuntimeError(f"Checksum mismatch for {item['id']}: {digest}")
        with zipfile.ZipFile(archive) as zf: zf.extractall(target)
        archive.unlink(missing_ok=True)
    def verify(self,model_id:str)->dict:
        item=self.entry(model_id); path=self.path(model_id); missing=[]
        if item.get("inventory"):
            inventory=json.loads((self.manifest_path.parent/item["inventory"]).read_text())
            allowed=item.get("allow_patterns")
            import fnmatch
            for row in inventory["siblings"]:
                rel=row["rfilename"]
                if allowed and not any(fnmatch.fnmatch(rel,p) for p in allowed): continue
                if not (path/rel).exists(): missing.append(rel)
        return {"id":model_id,"installed":self.is_installed(model_id),"revision":item["revision"],"missing":missing,"ok":self.is_installed(model_id) and not missing}
    def remove(self, model_id: str) -> None: shutil.rmtree(self.path(model_id),ignore_errors=True)
