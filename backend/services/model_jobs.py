from __future__ import annotations
from ..jobs import JobManager,JobRecord
from ..models import ModelManager

def submit_model_download(manager:ModelManager,jobs:JobManager,model_id:str)->JobRecord:
    manager.entry(model_id)
    def run(ctx):
        ctx.report(.02,'Preparing model download');path=manager.download(model_id);ctx.report(.98,'Download complete; writing marker');return {'modelId':model_id,'path':str(path)}
    return jobs.submit(f'model-download:{model_id}',run,uses_gpu=False)
