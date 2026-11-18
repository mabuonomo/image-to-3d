"use client";

import { useEffect, useState } from "react";
import ModelViewer from "@/components/ModelViewer";

const WORKER_URL =
  process.env.NEXT_PUBLIC_WORKER_URL || "http://localhost:8000";

interface GpuDevice {
  name: string;
  vram_gb: number;
  compute_capability: string;
}

interface HealthResponse {
  status: string;
  pipeline_mode: string;
  gpu: {
    cuda_available: boolean;
    cuda_version: string | null;
    devices: GpuDevice[];
  };
}

interface JobResponse {
  job_id: string;
  status: string;
  progress: number;
  step: string;
  output_url: string | null;
  error: string | null;
}

export default function HomePage() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [removeBg, setRemoveBg] = useState(true);
  const [autoRig, setAutoRig] = useState(true);
  const [job, setJob] = useState<JobResponse | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetch(`${WORKER_URL}/health`)
      .then((res) => res.json())
      .then(setHealth)
      .catch(() => setHealth(null));
  }, []);

  useEffect(() => {
    if (!job || job.status === "completed" || job.status === "failed") return;
    const timer = setInterval(async () => {
      try {
        const res = await fetch(`${WORKER_URL}/jobs/${job.job_id}`);
        if (res.ok) {
          const data: JobResponse = await res.json();
          setJob(data);
        }
      } catch {
        // Ignore transient polling error
      }
    }, 1000);
    return () => clearInterval(timer);
  }, [job]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0] || null;
    setFile(selected);
    if (selected) {
      setPreviewUrl(URL.createObjectURL(selected));
    } else {
      setPreviewUrl(null);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setSubmitting(true);
    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("remove_bg", String(removeBg));
      formData.append("auto_rig", String(autoRig));

      const res = await fetch(`${WORKER_URL}/jobs`, {
        method: "POST",
        body: formData,
      });
      if (!res.ok) {
        throw new Error(`Errore HTTP ${res.status}`);
      }
      const data: JobResponse = await res.json();
      setJob(data);
    } catch (err) {
      alert(err instanceof Error ? err.message : "Errore invio job");
    } finally {
      setSubmitting(false);
    }
  };

  const glbUrl =
    job?.status === "completed" && job.output_url
      ? `${WORKER_URL}${job.output_url}`
      : null;

  const gpuDevice = health?.gpu.devices?.[0];

  return (
    <main className="max-w-6xl mx-auto px-6 py-8 space-y-6">
      <header className="flex flex-wrap items-center justify-between gap-4 border-b border-zinc-800 pb-5">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            Image-to-3D Rigging Studio
          </h1>
          <p className="text-sm text-zinc-400">
            Genera modelli <code>.glb</code> con scheletro per animazioni e video
          </p>
        </div>

        <div className="flex items-center gap-3 text-xs bg-zinc-900 border border-zinc-800 rounded-lg px-3.5 py-2">
          <span
            className={`w-2.5 h-2.5 rounded-full ${
              health?.gpu.cuda_available ? "bg-emerald-400" : "bg-amber-400"
            }`}
          />
          {health ? (
            <span>
              {gpuDevice
                ? `${gpuDevice.name} (${gpuDevice.vram_gb} GB) • CUDA ${health.gpu.cuda_version}`
                : "Worker attivo (CPU fallback)"}{" "}
              • Modalità: <strong>{health.pipeline_mode}</strong>
            </span>
          ) : (
            <span className="text-zinc-500">Worker non raggiungibile</span>
          )}
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <section className="lg:col-span-4 space-y-4">
          <form
            onSubmit={handleSubmit}
            className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-5 space-y-4"
          >
            <div>
              <label className="block text-sm font-medium mb-2">
                Immagine di partenza (A-pose / T-pose consigliata)
              </label>
              <input
                type="file"
                accept="image/*"
                onChange={handleFileChange}
                className="block w-full text-xs text-zinc-400 file:mr-3 file:py-2 file:px-3 file:rounded-lg file:border-0 file:bg-zinc-800 file:text-zinc-200 hover:file:bg-zinc-700 cursor-pointer"
              />
            </div>

            {previewUrl && (
              <div className="rounded-lg border border-zinc-800 overflow-hidden bg-zinc-950 p-2">
                <img
                  src={previewUrl}
                  alt="Anteprima"
                  className="max-h-48 mx-auto object-contain"
                />
              </div>
            )}

            <div className="space-y-2 pt-1">
              <label className="flex items-center gap-2 text-sm text-zinc-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={removeBg}
                  onChange={(e) => setRemoveBg(e.target.checked)}
                  className="rounded border-zinc-700 bg-zinc-800"
                />
                Rimuovi sfondo automaticamente
              </label>

              <label className="flex items-center gap-2 text-sm text-zinc-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={autoRig}
                  onChange={(e) => setAutoRig(e.target.checked)}
                  className="rounded border-zinc-700 bg-zinc-800"
                />
                Auto-Rigging (aggiungi scheletro)
              </label>
            </div>

            <button
              type="submit"
              disabled={!file || submitting}
              className="w-full py-2.5 px-4 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-40 font-medium text-sm transition"
            >
              {submitting ? "Invio in corso..." : "Genera .GLB con Scheletro"}
            </button>
          </form>

          {job && (
            <div className="bg-zinc-900/60 border border-zinc-800 rounded-xl p-5 space-y-3">
              <div className="flex items-center justify-between text-xs">
                <span className="text-zinc-400">Job #{job.job_id}</span>
                <span className="uppercase font-semibold text-indigo-400">
                  {job.status}
                </span>
              </div>

              <div className="w-full bg-zinc-800 rounded-full h-2 overflow-hidden">
                <div
                  className="bg-indigo-500 h-full transition-all duration-300"
                  style={{ width: `${job.progress}%` }}
                />
              </div>

              <p className="text-xs text-zinc-300">{job.step}</p>

              {job.error && (
                <p className="text-xs text-red-400 bg-red-950/40 border border-red-900 rounded p-2">
                  {job.error}
                </p>
              )}

              {glbUrl && (
                <a
                  href={glbUrl}
                  download={`${job.job_id}.glb`}
                  className="block text-center w-full py-2 px-3 rounded-lg border border-emerald-700 bg-emerald-950/50 hover:bg-emerald-900/50 text-emerald-300 text-xs font-medium transition"
                >
                  Scarica {job.job_id}.glb
                </a>
              )}
            </div>
          )}
        </section>

        <section className="lg:col-span-8">
          <ModelViewer glbUrl={glbUrl} />
        </section>
      </div>
    </main>
  );
}
