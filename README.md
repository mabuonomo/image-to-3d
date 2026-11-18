# 🎨 Image-to-3D

A local-first application to generate **rigged `.glb` 3D models (with skeleton/armature & skinning)** from a single image, designed for animation and video creation. Powered by **Next.js** on the frontend and **FastAPI + Hunyuan3D-2 + UniRig + Blender** on the **CUDA 12.8** GPU worker (targeted for **NVIDIA RTX 5080 / Blackwell**).

## 🏗️ Architecture

```text
image-to-3d/
├── docker-compose.yml        # Next.js + GPU Worker orchestration (NVIDIA runtime)
├── .env.example              # Environment variable template
├── data/
│   ├── uploads/              # Uploaded & preprocessed images
│   └── outputs/              # Generated .glb and intermediate .fbx files
├── models/                   # Cached HuggingFace model weights (persisted volume)
└── apps/
    ├── web/                  # Next.js + Three.js frontend (SkeletonHelper + Video Recorder)
    └── worker/               # Python FastAPI + PyTorch CUDA 12.8 backend
        └── app/
            ├── main.py       # REST API + sequential GPU job queue (1 job at a time)
            ├── gpu_check.py  # CUDA / RTX 5080 diagnostics
            └── pipeline/
                ├── preprocess.py  # Background removal (rembg) & centering
                ├── mesh_gen.py    # Stage 1: Hunyuan3D-2 shape + PBR texture generation
                ├── auto_rig.py    # Stage 2: UniRig skeleton + skinning prediction
                └── fbx_to_glb.py  # Stage 3: Blender headless FBX -> GLB export
```

## 📋 Prerequisites

1. **🐳 Docker & Docker Compose**
2. **⚡ NVIDIA Drivers** + **NVIDIA Container Toolkit** installed and configured so Docker can access your GPU:
   ```bash
   docker run --rm --gpus all nvidia/cuda:12.8.0-base-ubuntu24.04 nvidia-smi
   ```

## 🚀 Quick Start

1. Create your `.env` file from the template:
   ```bash
   cp .env.example .env
   ```

2. Build and start the containers (the first build compiles CUDA extensions for Hunyuan3D-2 and sets up UniRig):
   ```bash
   docker compose up --build
   ```

3. Open in your browser:
   - **🌐 Next.js Frontend:** http://localhost:3000
   - **⚙️ Worker API / Health:** http://localhost:8000/health

> 💡 **Note on first run:** Model weights for `tencent/Hunyuan3D-2mini` and `UniRig` are downloaded automatically into `./models` on the first generation job and cached for subsequent runs.

## 🔍 Verify GPU Access (RTX 5080)

Check that PyTorch inside the worker container detects your RTX 5080 and CUDA 12.8:

```bash
docker compose exec worker python -m app.gpu_check
```

## 🔄 Pipeline Overview

1. **✂️ Preprocessing (`preprocess.py`):** Removes the background with `rembg` and centers the subject on a 1024×1024 RGBA canvas (A-pose or T-pose character images work best for auto-rigging).
2. **🧊 3D Mesh & Texture (`mesh_gen.py`):** Runs **Hunyuan3D-2** (`tencent/Hunyuan3D-2mini` by default) in `float16`, then unloads the shape pipeline before running texture painting (`Hunyuan3DPaintPipeline`) to stay comfortably within 16 GB VRAM.
3. **🦴 Auto-Rigging (`auto_rig.py` + `fbx_to_glb.py`):** Runs **UniRig** (`generate_skeleton.sh` → `generate_skin.sh`) in an isolated virtualenv, then converts the rigged `.fbx` to a web-ready `.glb` via **Blender headless**.

## 🎬 Video Creation

Inside the Next.js 3D viewer you can:
* 🦴 Toggle bone visibility (**Mostra/Nascondi Ossa**).
* ▶️ Control animation playback (**Play / Pausa**) if animations are present.
* 🎥 Record the 3D canvas directly to **`.webm`** via **Registra Video (.webm)**.
* 💾 Download the rigged **`.glb`** for Blender, Unreal, or Unity.
