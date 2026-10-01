from __future__ import annotations
import os, shutil, subprocess
from pathlib import Path
from .base import ImageRequest

class QwenImage21NcnnProvider:
    """Portable ncnn/Vulkan backend for Windows low-VRAM GPUs.

    Runtime release 20260928; model revision is pinned by ModelManager.
    It supports T2I, editing, up to ten references and RGBA output.
    """
    def __init__(self, runtime_dir: Path, model_dir: Path, gpu_id: int = 0):
        self.runtime_dir, self.model_dir, self.gpu_id = runtime_dir, model_dir, gpu_id
    def _find_exe(self)->Path:
        names=["qwenimage-ncnn-vulkan.exe","qwenimage-ncnn-vulkan"]
        for name in names:
            direct=self.runtime_dir/name
            if direct.exists(): return direct
            found=next(self.runtime_dir.rglob(name),None)
            if found:return found
        raise FileNotFoundError("Không tìm thấy qwenimage-ncnn-vulkan.exe; hãy cài runtime model package")
    def validate(self)->dict:
        exe=self._find_exe(); model=self.model_dir/"qwenimage21" if (self.model_dir/"qwenimage21").exists() else self.model_dir
        required=[model/"text_encoder/text_encoder.ncnn.bin",model/"transformer/blocks.ncnn.bin",model/"vae/decoder.ncnn.bin"]
        missing=[str(p) for p in required if not p.exists()]
        return {"ok":not missing,"executable":str(exe),"model":str(model),"missing":missing}
    def generate(self,request:ImageRequest)->Path:
        state=self.validate()
        if not state["ok"]: raise RuntimeError("Model ncnn chưa đầy đủ: "+", ".join(state["missing"]))
        if request.width%16 or request.height%16: raise ValueError("Kích thước text-to-image phải chia hết cho 16")
        request.output.parent.mkdir(parents=True,exist_ok=True)
        command=[state["executable"],"-m",state["model"],"-p",request.prompt,"-o",str(request.output),"-s",f"{request.width},{request.height}","-l",str(request.steps),"-r",str(request.seed),"-g",str(self.gpu_id)]
        if request.negative_prompt: command += ["-n",request.negative_prompt,"-w","4"]
        for image in request.input_images: command += ["-i",str(image)]
        creationflags=subprocess.CREATE_NO_WINDOW if os.name=="nt" else 0
        result=subprocess.run(command,cwd=self.runtime_dir,capture_output=True,text=True,creationflags=creationflags)
        if result.returncode: raise RuntimeError(f"ncnn failed ({result.returncode}): {result.stderr[-2000:]}")
        if not request.output.exists(): raise RuntimeError("ncnn completed but output was not created")
        return request.output
    def unload(self)->None: pass
