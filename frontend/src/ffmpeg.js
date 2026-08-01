import { FFmpeg } from "@ffmpeg/ffmpeg";
import { fetchFile, toBlobURL } from "@ffmpeg/util";

const MT_BASE = "https://unpkg.com/@ffmpeg/core-mt@0.12.6/dist/umd";
const ST_BASE = "https://unpkg.com/@ffmpeg/core@0.12.6/dist/umd";

const FONT_MAP = {
  Arial: { url: "https://cdn.jsdelivr.net/fontsource/fonts/arimo@latest/latin-400-normal.ttf", family: "Arimo" },
  Inter: { url: "https://cdn.jsdelivr.net/fontsource/fonts/inter@latest/latin-400-normal.ttf", family: "Inter" },
  Montserrat: { url: "https://cdn.jsdelivr.net/fontsource/fonts/montserrat@latest/latin-400-normal.ttf", family: "Montserrat" },
  Poppins: { url: "https://cdn.jsdelivr.net/fontsource/fonts/poppins@latest/latin-400-normal.ttf", family: "Poppins" },
  "Bebas Neue": { url: "https://cdn.jsdelivr.net/fontsource/fonts/bebas-neue@latest/latin-400-normal.ttf", family: "Bebas Neue" },
};
const FALLBACK_FONT = "Inter";

let loadPromise = null;
let onProgress = null;

async function createFFmpeg() {
  const instance = new FFmpeg();
  instance.on("progress", ({ progress }) => {
    onProgress?.(Math.min(100, Math.round(progress * 100)));
  });
  instance.on("log", ({ type, message }) => {
    console.log(`[ffmpeg ${type}]`, message);
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

function hexToAss(hex) {
  const h = String(hex || "#FFFFFF").replace("#", "");
  if (h.length === 6) {
    return `&H00${h.slice(4, 6)}${h.slice(2, 4)}${h.slice(0, 2)}`;
  }
  return "&H00FFFFFF";
}

function buildForceStyle(style, fontFamily) {
  const family = fontFamily || (FONT_MAP[style.font] || FONT_MAP[FALLBACK_FONT]).family;
  const bgOpacity = Math.max(0, Math.min(1, Number(style.bgOpacity ?? 0.7)));
  const backAlpha = Math.round(bgOpacity * 255)
    .toString(16)
    .padStart(2, "0")
    .toUpperCase();
  const marginV = { bottom: 50, top: 650, center: 360 }[style.position] ?? 50;
  return [
    `Fontname=${family}`,
    `Fontsize=${style.fontSize || 26}`,
    `PrimaryColour=${hexToAss(style.fontColor)}`,
    `OutlineColour=${hexToAss(style.bgColor)}`,
    `BackColour=&H${backAlpha}000000`,
    "BorderStyle=1",
    "Outline=2",
    "Shadow=1",
    "Alignment=2",
    `MarginV=${marginV}`,
  ].join(",");
}

async function loadFont(ffmpeg, family) {
  let source = FONT_MAP[family];
  if (!source) source = FONT_MAP[FALLBACK_FONT];
  let res = await fetch(source.url);
  if (!res.ok && source !== FONT_MAP[FALLBACK_FONT]) {
    source = FONT_MAP[FALLBACK_FONT];
    res = await fetch(source.url);
  }
  if (!res.ok) throw new Error(`Failed to load font ${source.family}`);
  await ffmpeg.writeFile(`tmp/${source.family}`, new Uint8Array(await res.arrayBuffer()));
  return source;
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

export async function burnSubtitles(file, srtContent, style, progress) {
  onProgress = progress;
  const instance = await loadFFmpeg();
  let loadedFont = null;
  try {
    await instance.writeFile("input", await fetchFile(file));
    await instance.writeFile("subs.srt", srtContent);
    loadedFont = await loadFont(instance, style.font);
    const forceStyle = buildForceStyle(style, loadedFont.family);
    await instance.exec([
      "-i", "input",
      "-vf",
      `subtitles=subs.srt:fontsdir=/tmp:force_style='${forceStyle}'`,
      "-c:v", "libx264",
      "-preset", "ultrafast",
      "-c:a", "aac",
      "-b:a", "192k",
      "-movflags", "+faststart",
      "output.mp4", "-y",
    ]);
    const data = await instance.readFile("output.mp4");
    return new Blob([data], { type: "video/mp4" });
  } finally {
    await instance.deleteFile("input").catch(() => {});
    await instance.deleteFile("subs.srt").catch(() => {});
    if (loadedFont) await instance.deleteFile(`tmp/${loadedFont.family}`).catch(() => {});
    await instance.deleteFile("output.mp4").catch(() => {});
    onProgress = null;
  }
}
