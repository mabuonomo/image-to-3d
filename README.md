# Image-to-3D Rigging Studio

Tool locale per generare modelli **`.glb` con scheletro (armature + skinning)** a partire da una singola immagine, pensato per creare animazioni e video, con **Next.js** sul frontend e **FastAPI + CUDA 12.8** sul worker GPU (ottimizzato per **NVIDIA RTX 5080 / Blackwell**).

## Architettura

```text
image-to-3d/
├── docker-compose.yml        # Orchestrazione Next.js + Worker GPU (NVIDIA runtime)
├── .env.example              # Variabili d'ambiente
├── data/
│   ├── uploads/              # Immagini caricate e pre-processate
│   └── outputs/              # File .glb generati
├── models/                   # Directory per i pesi dei modelli AI locali
└── apps/
    ├── web/                  # Frontend Next.js + Three.js (SkeletonHelper + Video Recorder)
    └── worker/               # Backend Python FastAPI + PyTorch CUDA 12.8
        └── app/
            ├── main.py       # API REST + coda sequenziale GPU (1 job alla volta)
            ├── gpu_check.py  # Diagnostica CUDA / RTX 5080
            └── pipeline/
                ├── preprocess.py  # Rimozione sfondo (rembg) e centratura
                ├── mesh_gen.py    # Fase 1: Image -> Mesh 3D statica
                └── auto_rig.py    # Fase 2: Mesh -> .glb con scheletro e animazione
```

## Prerequisiti

1. **Docker & Docker Compose**
2. **Driver NVIDIA** aggiornati + **NVIDIA Container Toolkit** installato e configurato su Linux, così Docker può accedere alla RTX 5080:
   ```bash
   # Verifica rapida che Docker veda la GPU
   docker run --rm --gpus all nvidia/cuda:12.8.0-base-ubuntu24.04 nvidia-smi
   ```

## Avvio rapido

1. Crea il file `.env` partendo dal template:
   ```bash
   cp .env.example .env
   ```

2. Avvia i container con build:
   ```bash
   docker compose up --build
   ```

3. Apri il browser su:
   - **Frontend Next.js:** http://localhost:3000
   - **Worker API / Health:** http://localhost:8000/health

## Verifica GPU (RTX 5080)

Puoi verificare che PyTorch dentro il container riconosca correttamente la RTX 5080 e CUDA 12.8 con:

```bash
docker compose exec worker python -m app.gpu_check
```

## Modalità `demo` vs `production`

* **`PIPELINE_MODE=demo` (default):**
  Esegue la rimozione sfondo sull'immagine caricata e genera un `.glb` procedurale completo di **scheletro umanoide (7 ossa)**, **skin weights** e **animazione (`IdleWave`)**. Serve per verificare subito l'intera pipeline Docker, il viewer Three.js (`SkeletonHelper`), la coda asincrona e la registrazione video `.webm` dal browser.

* **`PIPELINE_MODE=production`:**
  Per generare personaggi/oggetti reali dall'immagine:
  1. **Fase 1 (`apps/worker/app/pipeline/mesh_gen.py`):** integra un modello Image-to-3D locale come **Hunyuan3D 2.0** o **TRELLIS** (16 GB VRAM compatibili caricando i modelli in sequenza e usando `fp16`/offloading).
  2. **Fase 2 (`apps/worker/app/pipeline/auto_rig.py`):** integra un modello di Auto-Rigging come **UniRig** o **Make-It-Animatable** (+ eventuale post-processing con Blender headless) per generare lo scheletro ed esportare il `.glb` finale.

## Creazione Video

Nel viewer 3D di Next.js puoi:
* Attivare/disattivare la visualizzazione delle ossa (**Mostra/Nascondi Ossa**).
* Controllare la riproduzione dell'animazione (**Play / Pausa**).
* Registrare direttamente il canvas 3D in formato **`.webm`** tramite il pulsante **Registra Video (.webm)**.
