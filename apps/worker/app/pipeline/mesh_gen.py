import gc
import os
from pathlib import Path

import torch
from PIL import Image


def _clear_vram() -> None:
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def generate_static_mesh(
    image_path: Path,
    output_mesh_path: Path,
    enable_texture: bool = True,
) -> Path:
    """
    Generate a 3D mesh (.glb) from a preprocessed RGBA image using Hunyuan3D-2.
    Models are loaded in float16 and unloaded sequentially to fit comfortably
    within 16 GB VRAM (RTX 5080).
    """
    from hy3dgen.shapegen import Hunyuan3DDiTFlowMatchingPipeline

    output_mesh_path.parent.mkdir(parents=True, exist_ok=True)

    model_id = os.getenv("HUNYUAN_MODEL_ID", "tencent/Hunyuan3D-2mini")
    subfolder = os.getenv("HUNYUAN_SUBFOLDER", "hunyuan3d-dit-v2-mini")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if device == "cuda" else torch.float32

    image = Image.open(image_path).convert("RGBA")

    shape_pipeline = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained(
        model_id,
        subfolder=subfolder,
        torch_dtype=dtype,
        use_safetensors=True,
        device=device,
    )

    with torch.no_grad():
        mesh = shape_pipeline(image=image)[0]

    del shape_pipeline
    _clear_vram()

    if enable_texture and device == "cuda":
        try:
            from hy3dgen.texgen import Hunyuan3DPaintPipeline

            paint_pipeline = Hunyuan3DPaintPipeline.from_pretrained(
                "tencent/Hunyuan3D-2"
            )
            with torch.no_grad():
                mesh = paint_pipeline(mesh, image=image)
            del paint_pipeline
            _clear_vram()
        except Exception as exc:
            print(f"[mesh_gen] Texture generation skipped ({exc}); exporting untextured mesh")

    mesh.export(str(output_mesh_path))
    return output_mesh_path
