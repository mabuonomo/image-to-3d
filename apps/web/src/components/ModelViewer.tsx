"use client";

import { useEffect, useRef, useState } from "react";
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";

interface ModelViewerProps {
  glbUrl: string | null;
}

export default function ModelViewer({ glbUrl }: ModelViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const skeletonRef = useRef<THREE.SkeletonHelper | null>(null);
  const mixerRef = useRef<THREE.AnimationMixer | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);

  const [showSkeleton, setShowSkeleton] = useState(true);
  const [isPlaying, setIsPlaying] = useState(true);
  const [isRecording, setIsRecording] = useState(false);
  const [hasBones, setHasBones] = useState(false);
  const [animationCount, setAnimationCount] = useState(0);

  const isPlayingRef = useRef(isPlaying);
  isPlayingRef.current = isPlaying;

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x111114);

    const camera = new THREE.PerspectiveCamera(
      45,
      container.clientWidth / container.clientHeight,
      0.1,
      100
    );
    camera.position.set(2.2, 1.8, 3.2);

    const renderer = new THREE.WebGLRenderer({
      antialias: true,
      preserveDrawingBuffer: true,
    });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.innerHTML = "";
    container.appendChild(renderer.domElement);
    canvasRef.current = renderer.domElement;

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.target.set(0, 1.0, 0);
    controls.enableDamping = true;

    const ambient = new THREE.AmbientLight(0xffffff, 0.8);
    scene.add(ambient);

    const dirLight = new THREE.DirectionalLight(0xffffff, 1.6);
    dirLight.position.set(3, 5, 4);
    scene.add(dirLight);

    const backLight = new THREE.DirectionalLight(0x88aaff, 0.7);
    backLight.position.set(-3, 2, -4);
    scene.add(backLight);

    const grid = new THREE.GridHelper(6, 12, 0x3f3f46, 0x27272a);
    scene.add(grid);

    let currentRoot: THREE.Object3D | null = null;
    skeletonRef.current = null;
    mixerRef.current = null;
    setHasBones(false);
    setAnimationCount(0);

    if (glbUrl) {
      const loader = new GLTFLoader();
      loader.load(
        glbUrl,
        (gltf) => {
          currentRoot = gltf.scene;
          scene.add(currentRoot);

          let foundBone = false;
          currentRoot.traverse((obj) => {
            if ((obj as THREE.Bone).isBone) {
              foundBone = true;
            }
          });
          setHasBones(foundBone);

          if (foundBone) {
            const helper = new THREE.SkeletonHelper(currentRoot);
            helper.visible = showSkeleton;
            scene.add(helper);
            skeletonRef.current = helper;
          }

          if (gltf.animations.length > 0) {
            const mixer = new THREE.AnimationMixer(currentRoot);
            const action = mixer.clipAction(gltf.animations[0]);
            action.play();
            mixerRef.current = mixer;
            setAnimationCount(gltf.animations.length);
          }
        },
        undefined,
        (err) => {
          console.error("Errore caricamento GLB:", err);
        }
      );
    }

    const clock = new THREE.Clock();
    let frameId = 0;

    const animate = () => {
      frameId = requestAnimationFrame(animate);
      const delta = clock.getDelta();
      if (mixerRef.current && isPlayingRef.current) {
        mixerRef.current.update(delta);
      }
      controls.update();
      renderer.render(scene, camera);
    };
    animate();

    const handleResize = () => {
      if (!container) return;
      camera.aspect = container.clientWidth / container.clientHeight;
      camera.updateProjectionMatrix();
      renderer.setSize(container.clientWidth, container.clientHeight);
    };
    window.addEventListener("resize", handleResize);

    return () => {
      cancelAnimationFrame(frameId);
      window.removeEventListener("resize", handleResize);
      controls.dispose();
      renderer.dispose();
    };
  }, [glbUrl]);

  useEffect(() => {
    if (skeletonRef.current) {
      skeletonRef.current.visible = showSkeleton;
    }
  }, [showSkeleton]);

  const toggleRecording = () => {
    if (isRecording && mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      return;
    }

    const canvas = canvasRef.current;
    if (!canvas) return;

    const stream = canvas.captureStream(30);
    const recorder = new MediaRecorder(stream, {
      mimeType: "video/webm;codecs=vp9",
    });
    const chunks: BlobPart[] = [];

    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) chunks.push(e.data);
    };

    recorder.onstop = () => {
      const blob = new Blob(chunks, { type: "video/webm" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `character-video-${Date.now()}.webm`;
      a.click();
      URL.revokeObjectURL(url);
    };

    mediaRecorderRef.current = recorder;
    recorder.start();
    setIsRecording(true);
  };

  return (
    <div className="flex flex-col gap-3 h-full">
      <div className="flex flex-wrap items-center justify-between gap-2 bg-zinc-900/80 border border-zinc-800 rounded-xl px-4 py-2.5">
        <div className="flex items-center gap-3 text-xs text-zinc-400">
          <span>
            Scheletro:{" "}
            <strong className={hasBones ? "text-emerald-400" : "text-zinc-500"}>
              {hasBones ? "Presente" : "N/D"}
            </strong>
          </span>
          <span>
            Animazioni:{" "}
            <strong className="text-zinc-200">{animationCount}</strong>
          </span>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setShowSkeleton((v) => !v)}
            disabled={!hasBones}
            className="px-3 py-1.5 text-xs font-medium rounded-lg border border-zinc-700 bg-zinc-800 hover:bg-zinc-700 disabled:opacity-40 transition"
          >
            {showSkeleton ? "Nascondi Ossa" : "Mostra Ossa"}
          </button>

          <button
            type="button"
            onClick={() => setIsPlaying((v) => !v)}
            disabled={animationCount === 0}
            className="px-3 py-1.5 text-xs font-medium rounded-lg border border-zinc-700 bg-zinc-800 hover:bg-zinc-700 disabled:opacity-40 transition"
          >
            {isPlaying ? "Pausa" : "Play"}
          </button>

          <button
            type="button"
            onClick={toggleRecording}
            disabled={!glbUrl}
            className={`px-3 py-1.5 text-xs font-medium rounded-lg transition disabled:opacity-40 ${
              isRecording
                ? "bg-red-600 hover:bg-red-500 text-white"
                : "bg-indigo-600 hover:bg-indigo-500 text-white"
            }`}
          >
            {isRecording ? "Stop & Scarica Video" : "Registra Video (.webm)"}
          </button>
        </div>
      </div>

      <div
        ref={containerRef}
        className="w-full h-[500px] rounded-xl border border-zinc-800 overflow-hidden bg-zinc-950"
      />
    </div>
  );
}
