import { FFmpeg } from "@ffmpeg/ffmpeg";
import { fetchFile, toBlobURL } from "@ffmpeg/util";

const MT_BASE = "https://unpkg.com/@ffmpeg/core-mt@0.12.6/dist/umd";
const ST_BASE = "https://unpkg.com/@ffmpeg/core@0.12.6/dist/umd";

let loadPromise = null;
let onProgress = null;

async function createFFmpeg() {
  const instance = new FFmpeg();
  instance.on("progress", ({ progress }) => {
    onProgress?.(Math.min(100, Math.round(progress * 100)));
  });
  const useMT = typeof crossOriginIsolated === "boolean" && crossOriginIsolated;
  const base = useMT ? MT_BASE : ST_BASE;
  await instance.load({
    coreURL: await toBlobURL(`${base}/ffmpeg-core.js`, "text/javascript"),
    wasmURL: await toBlobURL(`${base}/ffmpeg-core.wasm`, "application/wasm"),
  });
  return instance;
}

export function loadFFmpeg() {
  if (!loadPromise) loadPromise = createFFmpeg();
  return loadPromise;
}

export async function extractAudio(file, progress) {
  onProgress = progress;
  const instance = await loadFFmpeg();
  try {
    await instance.writeFile("input", await fetchFile(file));
    await instance.exec([
      "-i", "input",
      "-vn", "-acodec", "pcm_s16le",
      "-ar", "16000", "-ac", "1",
      "output.wav", "-y",
    ]);
    const data = await instance.readFile("output.wav");
    return new Blob([data], { type: "audio/wav" });
  } finally {
    await instance.deleteFile("input").catch(() => {});
    await instance.deleteFile("output.wav").catch(() => {});
    onProgress = null;
  }
}
