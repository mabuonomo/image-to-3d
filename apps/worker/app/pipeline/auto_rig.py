import os
import subprocess
from pathlib import Path

UNIRIG_DIR = Path(os.getenv("UNIRIG_DIR", "/opt/UniRig"))
UNIRIG_VENV_BIN = Path(os.getenv("UNIRIG_VENV_BIN", "/opt/unirig-venv/bin"))
FBX_TO_GLB_SCRIPT = Path(__file__).parent / "fbx_to_glb.py"


def _run_cmd(cmd: list[str], cwd: Path | None = None, env: dict | None = None) -> None:
    result = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed ({' '.join(cmd)}):\n{result.stderr or result.stdout}"
        )


def rig_mesh(
    static_mesh_path: Path,
    output_rigged_path: Path,
    enable_rigging: bool = True,
) -> Path:
    """
    Run UniRig (skeleton prediction + skinning weight prediction) on a static .glb,
    then convert the resulting rigged .fbx to .glb via Blender headless.
    """
    if not enable_rigging:
        return static_mesh_path

    work_dir = output_rigged_path.parent
    skeleton_fbx = work_dir / f"{output_rigged_path.stem}_skeleton.fbx"
    skinned_fbx = work_dir / f"{output_rigged_path.stem}_skinned.fbx"

    env = os.environ.copy()
    env["PATH"] = f"{UNIRIG_VENV_BIN}:{env.get('PATH', '')}"

    # Step 1: Skeleton Prediction
    _run_cmd(
        [
            "bash",
            "launch/inference/generate_skeleton.sh",
            "--input",
            str(static_mesh_path),
            "--output",
            str(skeleton_fbx),
        ],
        cwd=UNIRIG_DIR,
        env=env,
    )

    # Step 2: Skinning Weight Prediction
    _run_cmd(
        [
            "bash",
            "launch/inference/generate_skin.sh",
            "--input",
            str(skeleton_fbx),
            "--output",
            str(skinned_fbx),
        ],
        cwd=UNIRIG_DIR,
        env=env,
    )

    # Step 3: Convert rigged FBX -> GLB via Blender headless
    _run_cmd(
        [
            "blender",
            "--background",
            "--python",
            str(FBX_TO_GLB_SCRIPT),
            "--",
            str(skinned_fbx),
            str(output_rigged_path),
        ]
    )

    return output_rigged_path
