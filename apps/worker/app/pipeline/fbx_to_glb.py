"""Blender headless script: convert a rigged FBX from UniRig into a .glb file."""
import sys
import bpy


def main() -> None:
    argv = sys.argv
    if "--" not in argv:
        raise RuntimeError("Usage: blender --background --python fbx_to_glb.py -- <input.fbx> <output.glb>")
    args = argv[argv.index("--") + 1 :]
    if len(args) < 2:
        raise RuntimeError("Expected <input.fbx> <output.glb>")

    input_fbx, output_glb = args[0], args[1]

    # Clear default scene
    bpy.ops.wm.read_factory_settings(use_empty=True)

    # Import rigged FBX
    bpy.ops.import_scene.fbx(filepath=input_fbx, automatic_bone_orientation=True)

    # Export as GLB with armature/skinning preserved
    bpy.ops.export_scene.gltf(
        filepath=output_glb,
        export_format="GLB",
        export_skins=True,
        export_animations=True,
        export_yup=True,
    )


if __name__ == "__main__":
    main()
