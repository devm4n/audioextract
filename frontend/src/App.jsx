import axios from "axios";
import { useState, useRef } from "react";

const STYLES = {
  fonts: ["Arial", "Inter", "Montserrat", "Poppins", "Bebas Neue"],
  positions: [
    { value: "bottom", label: "Bottom" },
    { value: "center", label: "Center" },
    { value: "top", label: "Top" },
  ],
};

export default function App() {
  const [file, setFile] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef(null);
  const [style, setStyle] = useState({
    font: "Inter",
    fontSize: 26,
    fontColor: "#ffffff",
    bgColor: "#000000",
    bgOpacity: 0.7,
    position: "bottom",
    maxWords: 8,
  });
  const apiUrl = (import.meta.env.VITE_API_URL || "").replace(/\/+$/, "");

  const handleFile = (f) => {
    if (f) setFile(f);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragging(false);
    handleFile(e.dataTransfer.files[0]);
  };

  const handleSubmit = async () => {
    const form = new FormData();
    form.append("video_file", file);
    form.append("caption_style", JSON.stringify(style));
    setLoading(true);
    setError("");
    setResult(null);
    try {
      const response = await axios.post(`${apiUrl}/upload/`, form, {
        timeout: 180000,
        headers: { "Content-Type": "multipart/form-data" },
      });
      setResult(response.data);
    } catch (err) {
      setError(err.response?.data?.video_file?.[0] || err.response?.data?.error || "Upload failed");
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (url, filename) => {
    const res = await fetch(url);
    const blob = await res.blob();
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  const dropProps = {
    onDragOver: (e) => { e.preventDefault(); setDragging(true); },
    onDragLeave: () => setDragging(false),
    onDrop: handleDrop,
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-zinc-950 via-zinc-900 to-zinc-950 flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-lg">

        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold bg-gradient-to-r from-emerald-400 to-cyan-400 bg-clip-text text-transparent">
            CapDamn!
          </h1>
        </div>

        <label
          {...dropProps}
          className={`relative block w-full border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-200 group overflow-hidden ${
            dragging
              ? "border-emerald-400 bg-emerald-500/10 scale-[1.02]"
              : file
                ? "border-emerald-500/50 bg-emerald-500/5"
                : "border-zinc-700 hover:border-zinc-500 bg-zinc-900/50"
          }`}
          onClick={() => !loading && inputRef.current?.click()}
        >
          <div className={`absolute inset-0 bg-gradient-to-br from-emerald-500/5 to-transparent pointer-events-none transition-opacity ${dragging ? "opacity-100" : "opacity-0"}`} />
          <input
            ref={inputRef}
            type="file"
            accept="video/mp4,video/webm,video/x-matroska"
            className="hidden"
            disabled={loading}
            onChange={(e) => handleFile(e.target.files[0])}
          />
          <div className="relative">
            <svg className={`w-10 h-10 mx-auto mb-3 transition-colors duration-200 ${file ? "text-emerald-400" : dragging ? "text-emerald-300" : "text-zinc-600 group-hover:text-zinc-400"}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              {file ? (
                <path strokeLinecap="round" strokeLinejoin="round" d="m15.75 10.5 4.72-4.72a.75.75 0 0 1 1.28.53v11.38a.75.75 0 0 1-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 0 0 2.25-2.25v-9a2.25 2.25 0 0 0-2.25-2.25h-9A2.25 2.25 0 0 0 2.25 7.5v9a2.25 2.25 0 0 0 2.25 2.25Z" />
              ) : (
                <path strokeLinecap="round" strokeLinejoin="round" d="M3 16.5v2.25A2.25 2.25 0 0 0 5.25 21h13.5A2.25 2.25 0 0 0 21 18.75V16.5m-13.5-9L12 3m0 0 4.5 4.5M12 3v13.5" />
              )}
            </svg>
            <p className={`text-sm font-medium transition-colors duration-200 ${file ? "text-emerald-300" : dragging ? "text-emerald-200" : "text-zinc-400 group-hover:text-zinc-300"}`}>
              {file ? file.name : dragging ? "Drop it like it's hot" : "Drop video or click to choose"}
            </p>
            {!file && (
              <p className="text-zinc-600 text-xs mt-1">MP4, WebM, MKV &mdash; max 500MB</p>
            )}
          </div>
        </label>

        <div className="bg-zinc-800/40 backdrop-blur-sm rounded-xl p-5 mb-4 border border-zinc-800">
          <p className="text-zinc-400 text-xs uppercase tracking-wider mb-4 flex items-center gap-2">
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9.53 16.122a3 3 0 0 0-5.78 1.128 2.25 2.25 0 0 0 2.4 2.245 4.5 4.5 0 0 0 8.4-2.245c0-.399-.078-.78-.22-1.128Zm0 0a15.998 15.998 0 0 0 3.388-1.62m-5.043-.025a15.994 15.994 0 0 1 1.622-3.395m3.42 3.42a15.995 15.995 0 0 0 4.764-4.648l3.876-5.814a1.151 1.151 0 0 0-1.597-1.597L14.146 6.32a15.996 15.996 0 0 0-4.649 4.763m3.42 3.42a6.776 6.776 0 0 0-3.42-3.42" />
            </svg>
            Caption Style
          </p>

          <div className="grid grid-cols-2 gap-x-3 gap-y-4">
            <div>
              <label className="text-zinc-500 text-xs block mb-1.5">Words per subtitle</label>
              <input
                type="number" min={3} max={20}
                value={style.maxWords}
                disabled={loading}
                onChange={(e) => setStyle({ ...style, maxWords: Number(e.target.value) })}
                className="w-full bg-zinc-900/60 text-zinc-200 text-sm rounded-lg px-3 py-2 border border-zinc-700 focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/20 outline-none transition-all disabled:opacity-30"
              />
            </div>
            <div>
              <label className="text-zinc-500 text-xs block mb-1.5">Font</label>
              <select
                value={style.font} disabled={loading}
                onChange={(e) => setStyle({ ...style, font: e.target.value })}
                className="w-full bg-zinc-900/60 text-zinc-200 text-sm rounded-lg px-3 py-2 border border-zinc-700 focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/20 outline-none transition-all disabled:opacity-30 appearance-none"
              >
                {STYLES.fonts.map((f) => (<option key={f}>{f}</option>))}
              </select>
            </div>
            <div>
              <label className="text-zinc-500 text-xs block mb-1.5">Size</label>
              <input
                type="number" min={12} max={72}
                value={style.fontSize}
                disabled={loading}
                onChange={(e) => setStyle({ ...style, fontSize: Number(e.target.value) })}
                className="w-full bg-zinc-900/60 text-zinc-200 text-sm rounded-lg px-3 py-2 border border-zinc-700 focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/20 outline-none transition-all disabled:opacity-30"
              />
            </div>
            <div>
              <label className="text-zinc-500 text-xs block mb-1.5">Text Color</label>
              <div className="relative">
                <input
                  type="color"
                  value={style.fontColor}
                  disabled={loading}
                  onChange={(e) => setStyle({ ...style, fontColor: e.target.value })}
                  className="w-full h-9 rounded-lg cursor-pointer bg-zinc-900/60 border border-zinc-700 disabled:opacity-30 [&::-webkit-color-swatch-wrapper]:p-1 [&::-webkit-color-swatch]:rounded-md"
                />
              </div>
            </div>
            <div>
              <label className="text-zinc-500 text-xs block mb-1.5">BG Color</label>
              <div className="relative">
                <input
                  type="color"
                  value={style.bgColor}
                  disabled={loading}
                  onChange={(e) => setStyle({ ...style, bgColor: e.target.value })}
                  className="w-full h-9 rounded-lg cursor-pointer bg-zinc-900/60 border border-zinc-700 disabled:opacity-30 [&::-webkit-color-swatch-wrapper]:p-1 [&::-webkit-color-swatch]:rounded-md"
                />
              </div>
            </div>
            <div>
              <label className="text-zinc-500 text-xs block mb-1.5">Position</label>
              <select
                value={style.position} disabled={loading}
                onChange={(e) => setStyle({ ...style, position: e.target.value })}
                className="w-full bg-zinc-900/60 text-zinc-200 text-sm rounded-lg px-3 py-2 border border-zinc-700 focus:border-emerald-500/50 focus:ring-1 focus:ring-emerald-500/20 outline-none transition-all disabled:opacity-30 appearance-none"
              >
                {STYLES.positions.map((p) => (
                  <option key={p.value} value={p.value}>{p.label}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="mt-5 pt-4 border-t border-zinc-800">
            <div className="flex items-center justify-between mb-2">
              <label className="text-zinc-500 text-xs uppercase tracking-wider">Background Opacity</label>
              <span className="text-emerald-400 text-xs font-mono w-8 text-right">{Math.round(style.bgOpacity * 100)}%</span>
            </div>
            <div className="relative py-1">
              <input
                type="range" min={0} max={100}
                value={Math.round(style.bgOpacity * 100)}
                disabled={loading}
                onChange={(e) => setStyle({ ...style, bgOpacity: e.target.value / 100 })}
                className="w-full h-2 rounded-full appearance-none cursor-pointer bg-zinc-700 disabled:opacity-30
                  [&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:w-4 [&::-webkit-slider-thumb]:h-4 [&::-webkit-slider-thumb]:rounded-full [&::-webkit-slider-thumb]:bg-emerald-400 [&::-webkit-slider-thumb]:shadow-lg [&::-webkit-slider-thumb]:shadow-emerald-500/30 [&::-webkit-slider-thumb]:transition-transform [&::-webkit-slider-thumb]:hover:scale-125
                  [&::-moz-range-thumb]:w-4 [&::-moz-range-thumb]:h-4 [&::-moz-range-thumb]:rounded-full [&::-moz-range-thumb]:bg-emerald-400 [&::-moz-range-thumb]:border-0 [&::-moz-range-thumb]:shadow-lg [&::-moz-range-thumb]:shadow-emerald-500/30"
                style={{
                  background: `linear-gradient(to right, #34d399 ${style.bgOpacity * 100}%, #3f3f46 ${style.bgOpacity * 100}%)`,
                }}
              />
            </div>
          </div>
        </div>

        <button
          onClick={handleSubmit}
          disabled={!file || loading}
          className="w-full bg-gradient-to-r from-emerald-500 to-emerald-600 text-white text-sm font-semibold py-3 rounded-xl hover:from-emerald-400 hover:to-emerald-500 disabled:from-zinc-800 disabled:to-zinc-800 disabled:text-zinc-600 disabled:cursor-not-allowed transition-all duration-200 shadow-lg shadow-emerald-500/20 hover:shadow-emerald-500/30 active:scale-[0.98]"
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <span className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              Processing...
            </span>
          ) : "Generate Captions"}
        </button>

        {loading && (
          <div className="mt-5 flex flex-col items-center gap-2">
            <div className="flex gap-1">
              <span className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
              <span className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
              <span className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
            </div>
            <p className="text-zinc-500 text-xs">Transcribing &amp; rendering captions...</p>
          </div>
        )}

        {error && (
          <div className="mt-4 p-3 bg-red-500/10 border border-red-500/20 rounded-xl text-red-400 text-xs text-center">
            {error}
          </div>
        )}

        {result && !loading && (
          <div className="mt-6 space-y-4">
            <video
              src={result.captioned_video_url || result.captioned_video}
              controls
              className="w-full rounded-xl border border-zinc-800 shadow-xl"
            />
            <div className="grid grid-cols-3 gap-2">
              <button
                onClick={() => handleDownload(result.captioned_video_url || result.captioned_video, "captioned_video.mp4")}
                className="flex items-center justify-center gap-2 bg-emerald-500/10 text-emerald-400 text-sm py-2.5 rounded-xl border border-emerald-500/20 hover:bg-emerald-500 hover:text-white hover:border-emerald-500 transition-all duration-200"
              >
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="m9 12.75 3 3m0 0 3-3m-3 3v-7.5M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
                </svg>
                Video
              </button>
              {(result.subtitle_url || result.subtitle_file) && (
                <button
                  onClick={() => handleDownload(result.subtitle_url || result.subtitle_file, "captions.srt")}
                  className="flex items-center justify-center gap-2 bg-zinc-800/50 text-zinc-400 text-sm py-2.5 rounded-xl border border-zinc-700/50 hover:bg-zinc-700 hover:text-zinc-200 transition-all duration-200"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="m9 12.75 3 3m0 0 3-3m-3 3v-7.5M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
                  </svg>
                  SRT
                </button>
              )}
              {(result.audio_url || result.audio_file) && (
                <button
                  onClick={() => handleDownload(result.audio_url || result.audio_file, "audio.wav")}
                  className="flex items-center justify-center gap-2 bg-zinc-800/50 text-zinc-400 text-sm py-2.5 rounded-xl border border-zinc-700/50 hover:bg-zinc-700 hover:text-zinc-200 transition-all duration-200"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="m9 12.75 3 3m0 0 3-3m-3 3v-7.5M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />
                  </svg>
                  Audio
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
