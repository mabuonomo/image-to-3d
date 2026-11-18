import asyncio
import os
import time
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.gpu_check import check_gpu
from app.pipeline.auto_rig import rig_mesh
from app.pipeline.mesh_gen import generate_static_mesh
from app.pipeline.preprocess import preprocess_image

DATA_DIR = Path(os.getenv("DATA_DIR", "/data"))
UPLOADS_DIR = DATA_DIR / "uploads"
OUTPUTS_DIR = DATA_DIR / "outputs"
PIPELINE_MODE = os.getenv("PIPELINE_MODE", "demo")


class JobRecord(BaseModel):
    job_id: str
    status: Literal["queued", "preprocessing", "generating_mesh", "rigging", "completed", "failed"]
    progress: int
    step: str
    mode: str
    remove_bg: bool
    auto_rig: bool
    output_url: str | None = None
    error: str | None = None
    created_at: float


JOBS: dict[str, JobRecord] = {}
JOB_QUEUE: asyncio.Queue[str] = asyncio.Queue()


async def _process_job(job_id: str) -> None:
    job = JOBS[job_id]
    input_path = UPLOADS_DIR / f"{job_id}_input.png"
    pre_path = UPLOADS_DIR / f"{job_id}_clean.png"
    static_mesh_path = OUTPUTS_DIR / f"{job_id}_static.glb"
    final_mesh_path = OUTPUTS_DIR / f"{job_id}.glb"

    try:
        job.status = "preprocessing"
        job.progress = 20
        job.step = "Rimozione sfondo e normalizzazione immagine..."
        await asyncio.to_thread(
            preprocess_image, input_path, pre_path, job.remove_bg
        )

        job.status = "generating_mesh"
        job.progress = 55
        job.step = "Generazione mesh 3D..."
        await asyncio.to_thread(
            generate_static_mesh, pre_path, static_mesh_path, job.mode
        )

        job.status = "rigging"
        job.progress = 85
        job.step = "Auto-rigging scheletro e skinning..."
        result_path = await asyncio.to_thread(
            rig_mesh, static_mesh_path, final_mesh_path, job.auto_rig, job.mode
        )

        job.status = "completed"
        job.progress = 100
        job.step = "Modello .glb pronto"
        job.output_url = f"/outputs/{result_path.name}"
    except Exception as exc:
        job.status = "failed"
        job.progress = 0
        job.step = "Errore durante l'elaborazione"
        job.error = str(exc)


async def _worker_loop() -> None:
    """Process one GPU job at a time to avoid VRAM exhaustion."""
    while True:
        job_id = await JOB_QUEUE.get()
        try:
            if job_id in JOBS:
                await _process_job(job_id)
        finally:
            JOB_QUEUE.task_done()


@asynccontextmanager
async def lifespan(_: FastAPI):
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    task = asyncio.create_task(_worker_loop())
    yield
    task.cancel()


app = FastAPI(title="Image-to-3D GPU Worker", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "pipeline_mode": PIPELINE_MODE,
        "gpu": check_gpu(),
    }


@app.post("/jobs", response_model=JobRecord)
async def create_job(
    file: UploadFile = File(...),
    remove_bg: bool = Form(True),
    auto_rig: bool = Form(True),
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Il file deve essere un'immagine.")

    job_id = uuid.uuid4().hex[:12]
    input_path = UPLOADS_DIR / f"{job_id}_input.png"
    content = await file.read()
    input_path.write_bytes(content)

    record = JobRecord(
        job_id=job_id,
        status="queued",
        progress=5,
        step="In coda per la GPU...",
        mode=PIPELINE_MODE,
        remove_bg=remove_bg,
        auto_rig=auto_rig,
        created_at=time.time(),
    )
    JOBS[job_id] = record
    await JOB_QUEUE.put(job_id)
    return record


@app.get("/jobs/{job_id}", response_model=JobRecord)
def get_job(job_id: str):
    if job_id not in JOBS:
        raise HTTPException(status_code=404, detail="Job non trovato")
    return JOBS[job_id]


@app.get("/outputs/{filename}")
def get_output(filename: str):
    safe_name = Path(filename).name
    target = OUTPUTS_DIR / safe_name
    if not target.exists():
        raise HTTPException(status_code=404, detail="File non trovato")
    return FileResponse(
        path=target,
        media_type="model/gltf-binary",
        filename=safe_name,
    )
