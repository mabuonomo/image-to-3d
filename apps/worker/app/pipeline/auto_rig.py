from pathlib import Path
import struct
import numpy as np
import pygltflib


def _make_box(
    center: tuple[float, float, float],
    size: tuple[float, float, float],
    joint_index: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Create vertices, normals, indices, joints, and weights for an axis-aligned box."""
    cx, cy, cz = center
    hx, hy, hz = size[0] / 2.0, size[1] / 2.0, size[2] / 2.0

    # 6 faces x 4 vertices = 24 vertices for crisp per-face normals
    faces = [
        # +Z front
        ([cx - hx, cy - hy, cz + hz], [cx + hx, cy - hy, cz + hz], [cx + hx, cy + hy, cz + hz], [cx - hx, cy + hy, cz + hz], [0, 0, 1]),
        # -Z back
        ([cx + hx, cy - hy, cz - hz], [cx - hx, cy - hy, cz - hz], [cx - hx, cy + hy, cz - hz], [cx + hx, cy + hy, cz - hz], [0, 0, -1]),
        # +X right
        ([cx + hx, cy - hy, cz + hz], [cx + hx, cy - hy, cz - hz], [cx + hx, cy + hy, cz - hz], [cx + hx, cy + hy, cz + hz], [1, 0, 0]),
        # -X left
        ([cx - hx, cy - hy, cz - hz], [cx - hx, cy - hy, cz + hz], [cx - hx, cy + hy, cz + hz], [cx - hx, cy + hy, cz - hz], [-1, 0, 0]),
        # +Y top
        ([cx - hx, cy + hy, cz + hz], [cx + hx, cy + hy, cz + hz], [cx + hx, cy + hy, cz - hz], [cx - hx, cy + hy, cz - hz], [0, 1, 0]),
        # -Y bottom
        ([cx - hx, cy - hy, cz - hz], [cx + hx, cy - hy, cz - hz], [cx + hx, cy - hy, cz + hz], [cx - hx, cy - hy, cz + hz], [0, -1, 0]),
    ]

    verts = []
    norms = []
    idxs = []
    for f_idx, (v0, v1, v2, v3, n) in enumerate(faces):
        base = f_idx * 4
        verts.extend([v0, v1, v2, v3])
        norms.extend([n, n, n, n])
        idxs.extend([base, base + 1, base + 2, base, base + 2, base + 3])

    v_arr = np.array(verts, dtype=np.float32)
    n_arr = np.array(norms, dtype=np.float32)
    i_arr = np.array(idxs, dtype=np.uint16)
    j_arr = np.zeros((len(verts), 4), dtype=np.uint16)
    j_arr[:, 0] = joint_index
    w_arr = np.zeros((len(verts), 4), dtype=np.float32)
    w_arr[:, 0] = 1.0
    return v_arr, n_arr, i_arr, j_arr, w_arr


def _build_demo_rigged_glb(output_path: Path) -> Path:
    """
    Build a valid glTF 2.0 (.glb) humanoid figure with a hierarchical skeleton,
    skinning weights, and an IdleWave animation so the Next.js viewer,
    SkeletonHelper, and video recorder can be tested immediately.
    """
    # Joint hierarchy (indices in joint list 0..6):
    # 0: Hips (world y=0.9)
    # 1: Spine (local y=0.25 -> world y=1.15)
    # 2: Head (local y=0.45 -> world y=1.60)
    # 3: LeftArm (local x=-0.32, y=0.30 -> world x=-0.32, y=1.45)
    # 4: RightArm (local x=0.32, y=0.30 -> world x=0.32, y=1.45)
    # 5: LeftLeg (local x=-0.13, y=-0.10 -> world x=-0.13, y=0.80)
    # 6: RightLeg (local x=0.13, y=-0.10 -> world x=0.13, y=0.80)
    joint_defs = [
        ("Hips", [0.0, 0.90, 0.0], [1, 5, 6], (0.0, 0.90, 0.0)),
        ("Spine", [0.0, 0.25, 0.0], [2, 3, 4], (0.0, 1.15, 0.0)),
        ("Head", [0.0, 0.45, 0.0], [], (0.0, 1.60, 0.0)),
        ("LeftArm", [-0.32, 0.30, 0.0], [], (-0.32, 1.45, 0.0)),
        ("RightArm", [0.32, 0.30, 0.0], [], (0.32, 1.45, 0.0)),
        ("LeftLeg", [-0.13, -0.10, 0.0], [], (-0.13, 0.80, 0.0)),
        ("RightLeg", [0.13, -0.10, 0.0], [], (0.13, 0.80, 0.0)),
    ]

    parts = [
        _make_box((0.0, 0.92, 0.0), (0.36, 0.20, 0.22), 0),     # Hips
        _make_box((0.0, 1.25, 0.0), (0.42, 0.44, 0.24), 1),     # Torso/Spine
        _make_box((0.0, 1.68, 0.0), (0.26, 0.28, 0.26), 2),     # Head
        _make_box((-0.34, 1.22, 0.0), (0.14, 0.52, 0.14), 3),   # LeftArm
        _make_box((0.34, 1.22, 0.0), (0.14, 0.52, 0.14), 4),    # RightArm
        _make_box((-0.13, 0.44, 0.0), (0.16, 0.72, 0.18), 5),   # LeftLeg
        _make_box((0.13, 0.44, 0.0), (0.16, 0.72, 0.18), 6),    # RightLeg
    ]

    all_v, all_n, all_i, all_j, all_w = [], [], [], [], []
    vert_offset = 0
    for v, n, i, j, w in parts:
        all_v.append(v)
        all_n.append(n)
        all_i.append(i + vert_offset)
        all_j.append(j)
        all_w.append(w)
        vert_offset += len(v)

    positions = np.vstack(all_v).astype(np.float32)
    normals = np.vstack(all_n).astype(np.float32)
    indices = np.concatenate(all_i).astype(np.uint16)
    joints = np.vstack(all_j).astype(np.uint16)
    weights = np.vstack(all_w).astype(np.float32)

    # Inverse bind matrices (column-major 4x4 for glTF)
    ibms = []
    for _, _, _, world_pos in joint_defs:
        mat = np.eye(4, dtype=np.float32)
        mat[0, 3] = -world_pos[0]
        mat[1, 3] = -world_pos[1]
        mat[2, 3] = -world_pos[2]
        ibms.append(mat.T.flatten())
    ibm_arr = np.stack(ibms).astype(np.float32)

    # Simple 2-second looping animation on RightArm (wave) and Spine (subtle sway)
    anim_times = np.array([0.0, 0.5, 1.0, 1.5, 2.0], dtype=np.float32)
    # Quaternions [x, y, z, w] around Z axis for RightArm
    angles_arm = [0.0, 0.75, 1.15, 0.75, 0.0]
    arm_quats = np.array(
        [[0.0, 0.0, np.sin(a / 2.0), np.cos(a / 2.0)] for a in angles_arm],
        dtype=np.float32,
    )
    angles_spine = [0.0, -0.05, 0.0, 0.05, 0.0]
    spine_quats = np.array(
        [[0.0, np.sin(a / 2.0), 0.0, np.cos(a / 2.0)] for a in angles_spine],
        dtype=np.float32,
    )

    def pad4(b: bytes) -> bytes:
        rem = len(b) % 4
        return b + (b"\x00" * (4 - rem) if rem else b"")

    chunks = [
        pad4(positions.tobytes()),
        pad4(normals.tobytes()),
        pad4(joints.tobytes()),
        pad4(weights.tobytes()),
        pad4(indices.tobytes()),
        pad4(ibm_arr.tobytes()),
        pad4(anim_times.tobytes()),
        pad4(arm_quats.tobytes()),
        pad4(spine_quats.tobytes()),
    ]
    blob = b"".join(chunks)

    offsets = []
    cur = 0
    for c in chunks:
        offsets.append((cur, len(c)))
        cur += len(c)

    buffer_views = [
        pygltflib.BufferView(buffer=0, byteOffset=offsets[0][0], byteLength=len(positions.tobytes()), target=pygltflib.ARRAY_BUFFER),
        pygltflib.BufferView(buffer=0, byteOffset=offsets[1][0], byteLength=len(normals.tobytes()), target=pygltflib.ARRAY_BUFFER),
        pygltflib.BufferView(buffer=0, byteOffset=offsets[2][0], byteLength=len(joints.tobytes()), target=pygltflib.ARRAY_BUFFER),
        pygltflib.BufferView(buffer=0, byteOffset=offsets[3][0], byteLength=len(weights.tobytes()), target=pygltflib.ARRAY_BUFFER),
        pygltflib.BufferView(buffer=0, byteOffset=offsets[4][0], byteLength=len(indices.tobytes()), target=pygltflib.ELEMENT_ARRAY_BUFFER),
        pygltflib.BufferView(buffer=0, byteOffset=offsets[5][0], byteLength=len(ibm_arr.tobytes())),
        pygltflib.BufferView(buffer=0, byteOffset=offsets[6][0], byteLength=len(anim_times.tobytes())),
        pygltflib.BufferView(buffer=0, byteOffset=offsets[7][0], byteLength=len(arm_quats.tobytes())),
        pygltflib.BufferView(buffer=0, byteOffset=offsets[8][0], byteLength=len(spine_quats.tobytes())),
    ]

    pos_min = positions.min(axis=0).tolist()
    pos_max = positions.max(axis=0).tolist()

    accessors = [
        pygltflib.Accessor(bufferView=0, componentType=pygltflib.FLOAT, count=len(positions), type=pygltflib.VEC3, min=pos_min, max=pos_max),
        pygltflib.Accessor(bufferView=1, componentType=pygltflib.FLOAT, count=len(normals), type=pygltflib.VEC3),
        pygltflib.Accessor(bufferView=2, componentType=pygltflib.UNSIGNED_SHORT, count=len(joints), type=pygltflib.VEC4),
        pygltflib.Accessor(bufferView=3, componentType=pygltflib.FLOAT, count=len(weights), type=pygltflib.VEC4),
        pygltflib.Accessor(bufferView=4, componentType=pygltflib.UNSIGNED_SHORT, count=len(indices), type=pygltflib.SCALAR),
        pygltflib.Accessor(bufferView=5, componentType=pygltflib.FLOAT, count=len(joint_defs), type=pygltflib.MAT4),
        pygltflib.Accessor(bufferView=6, componentType=pygltflib.FLOAT, count=len(anim_times), type=pygltflib.SCALAR, min=[float(anim_times.min())], max=[float(anim_times.max())]),
        pygltflib.Accessor(bufferView=7, componentType=pygltflib.FLOAT, count=len(arm_quats), type=pygltflib.VEC4),
        pygltflib.Accessor(bufferView=8, componentType=pygltflib.FLOAT, count=len(spine_quats), type=pygltflib.VEC4),
    ]

    # Node 0 = Mesh node, Nodes 1..7 = Joint nodes (offset by +1)
    nodes = [pygltflib.Node(name="CharacterMesh", mesh=0, skin=0)]
    for name, translation, children, _ in joint_defs:
        nodes.append(
            pygltflib.Node(
                name=name,
                translation=translation,
                children=[c + 1 for c in children] if children else None,
            )
        )

    gltf = pygltflib.GLTF2(
        scene=0,
        scenes=[pygltflib.Scene(nodes=[0, 1])],
        nodes=nodes,
        meshes=[
            pygltflib.Mesh(
                name="DemoHumanoid",
                primitives=[
                    pygltflib.Primitive(
                        attributes=pygltflib.Attributes(
                            POSITION=0,
                            NORMAL=1,
                            JOINTS_0=2,
                            WEIGHTS_0=3,
                        ),
                        indices=4,
                        material=0,
                    )
                ],
            )
        ],
        materials=[
            pygltflib.Material(
                name="CharacterMaterial",
                pbrMetallicRoughness=pygltflib.PbrMetallicRoughness(
                    baseColorFactor=[0.35, 0.62, 0.95, 1.0],
                    metallicFactor=0.1,
                    roughnessFactor=0.55,
                ),
            )
        ],
        skins=[
            pygltflib.Skin(
                name="HumanoidSkeleton",
                inverseBindMatrices=5,
                skeleton=1,
                joints=[1, 2, 3, 4, 5, 6, 7],
            )
        ],
        animations=[
            pygltflib.Animation(
                name="IdleWave",
                samplers=[
                    pygltflib.AnimationSampler(input=6, output=7, interpolation="LINEAR"),
                    pygltflib.AnimationSampler(input=6, output=8, interpolation="LINEAR"),
                ],
                channels=[
                    pygltflib.AnimationChannel(
                        sampler=0,
                        target=pygltflib.AnimationChannelTarget(node=5, path="rotation"),  # RightArm
                    ),
                    pygltflib.AnimationChannel(
                        sampler=1,
                        target=pygltflib.AnimationChannelTarget(node=2, path="rotation"),  # Spine
                    ),
                ],
            )
        ],
        buffers=[pygltflib.Buffer(byteLength=len(blob))],
        bufferViews=buffer_views,
        accessors=accessors,
    )
    gltf.set_binary_blob(blob)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    gltf.save_binary(str(output_path))
    return output_path


def rig_mesh(
    static_mesh_path: Path,
    output_rigged_path: Path,
    enable_rigging: bool = True,
    mode: str = "demo",
) -> Path:
    """
    Add a skeleton (armature + skinning weights) to a 3D mesh and export as .glb.
    """
    if mode == "demo":
        return _build_demo_rigged_glb(output_rigged_path)

    if not enable_rigging:
        return static_mesh_path

    raise NotImplementedError(
        "Production auto-rigging (UniRig / Blender Headless) not yet wired. "
        "Set PIPELINE_MODE=demo to test with the procedural rigged .glb."
    )
