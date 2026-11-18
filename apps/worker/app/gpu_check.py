import torch


def check_gpu() -> dict:
    """Return CUDA and GPU diagnostics for health checks and CLI verification."""
    cuda_available = torch.cuda.is_available()
    info = {
        "torch_version": torch.__version__,
        "cuda_available": cuda_available,
        "cuda_version": torch.version.cuda,
        "device_count": torch.cuda.device_count() if cuda_available else 0,
        "devices": [],
    }
    if cuda_available:
        for idx in range(torch.cuda.device_count()):
            props = torch.cuda.get_device_properties(idx)
            info["devices"].append(
                {
                    "index": idx,
                    "name": props.name,
                    "vram_gb": round(props.total_memory / (1024**3), 2),
                    "compute_capability": f"{props.major}.{props.minor}",
                }
            )
    return info


if __name__ == "__main__":
    import json

    print(json.dumps(check_gpu(), indent=2))
