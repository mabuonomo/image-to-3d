FROM nvidia/cuda:12.8.0-devel-ubuntu24.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TORCH_CUDA_ARCH_LIST="8.9;9.0;12.0+PTX" \
    FORCE_CUDA=1 \
    PATH="/opt/venv/bin:$PATH"

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-dev \
    python3-pip \
    python3-venv \
    git \
    curl \
    ffmpeg \
    blender \
    build-essential \
    cmake \
    ninja-build \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    libxrender1 \
    libxi6 \
    && rm -rf /var/lib/apt/lists/*

# 1. Main venv for FastAPI + Hunyuan3D-2 (CUDA 12.8 for RTX 5080 Blackwell)
RUN python3 -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir --upgrade pip setuptools wheel && \
    /opt/venv/bin/pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cu128

WORKDIR /opt
RUN git clone --depth 1 https://github.com/Tencent-Hunyuan/Hunyuan3D-2.git /opt/Hunyuan3D-2 && \
    /opt/venv/bin/pip install --no-cache-dir -r /opt/Hunyuan3D-2/requirements.txt && \
    /opt/venv/bin/pip install --no-cache-dir -e /opt/Hunyuan3D-2 && \
    cd /opt/Hunyuan3D-2/hy3dgen/texgen/custom_rasterizer && /opt/venv/bin/python setup.py install && \
    cd /opt/Hunyuan3D-2/hy3dgen/texgen/differentiable_renderer && /opt/venv/bin/python setup.py install

# 2. Isolated venv for UniRig (auto-rigging & skinning)
RUN python3 -m venv /opt/unirig-venv && \
    /opt/unirig-venv/bin/pip install --no-cache-dir --upgrade pip setuptools wheel && \
    /opt/unirig-venv/bin/pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cu128 && \
    git clone --depth 1 https://github.com/VAST-AI-Research/UniRig.git /opt/UniRig && \
    /opt/unirig-venv/bin/pip install --no-cache-dir -r /opt/UniRig/requirements.txt

WORKDIR /app

COPY requirements.txt .
RUN /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

COPY app ./app

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
