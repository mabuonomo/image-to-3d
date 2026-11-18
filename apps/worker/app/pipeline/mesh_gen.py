import os
from pathlib import Path


def generate_static_mesh(
    image_path: Path,
    output_mesh_path: Path,
    mode: str = "demo",
) -> Path:
    """
    Generate a static 3D mesh (.glb) from a preprocessed image.

    In 'demo' mode, returns a marker path so the rigged demo builder can
    produce an immediate test asset.
    In 'production' mode, hook in Hunyuan3D 2.0 or TRELLIS here.
    """
    output_mesh_path.parent.mkdir(parents=True, exist_ok=True)

    if mode == "demo":
        # Demo mode skips heavy diffusion weights and delegates to auto_rig
        # which builds a procedural rigged humanoid .glb for end-to-end testing.
        return output_mesh_path

    models_dir = Path(os.getenv("MODELS_DIR", "/models"))
    raise NotImplementedError(
        f"Production Image-to-3D model not yet configured in {models_dir}. "
        "Install Hunyuan3D 2.0 or TRELLIS in apps/worker and wire it in mesh_gen.py, "
        "or set PIPELINE_MODE=demo to test the end-to-end pipeline."
    )
