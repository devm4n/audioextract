import axios from "axios";
import { useState } from "react";

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
  const [style, setStyle] = useState({
    font: "Inter",
    fontSize: 26,
    fontColor: "#ffffff",
    bgColor: "#000000",
    bgOpacity: 0.7,
    position: "bottom",
    maxWords: 8,
  });
  const apiUrl = import.meta.env.VITE_API_URL;

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

  return (
    <div className="bg-zinc-950 min-h-screen flex flex-col items-center justify-center font-mono p-4">
      <div className="w-full max-w-lg">
        <h2 className="text-zinc-500 text-xl uppercase tracking-widest mb-6 text-center">
          CaptionGen
        </h2>

        <label className="block w-full border border-dashed border-zinc-700 rounded p-6 text-center cursor-pointer hover:border-emerald-500 transition-colors group mb-4">
          <span className="text-zinc-400 text-sm group-hover:text-emerald-400 transition-colors">
            {file ? file.name : "drop video or click to choose"}
          </span>
          <input
            type="file"
            accept="video/mp4,video/webm,video/x-matroska"
            className="hidden"
            disabled={loading}
            onChange={(e) => setFile(e.target.files[0])}
          />
        </label>

        <div className="bg-zinc-900 rounded p-4 mb-4 space-y-3">
          <p className="text-zinc-400 text-xs uppercase tracking-wider">
            Caption Style
          </p>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-zinc-500 text-xs block mb-1">Words per subtitle</label>
              <input
                type="number"
                min={3}
                max={20}
                value={style.maxWords}
                disabled={loading}
                onChange={(e) =>
                  setStyle({ ...style, maxWords: Number(e.target.value) })
                }
                className="w-full bg-zinc-800 text-zinc-300 text-sm rounded px-2 py-1.5 border border-zinc-700 disabled:opacity-30"
              />
            </div>
            <div>
              <label className="text-zinc-500 text-xs block mb-1">Font</label>
              <select
                value={style.font}
                disabled={loading}
                onChange={(e) => setStyle({ ...style, font: e.target.value })}
                className="w-full bg-zinc-800 text-zinc-300 text-sm rounded px-2 py-1.5 border border-zinc-700 disabled:opacity-30"
              >
                {STYLES.fonts.map((f) => (
                  <option key={f}>{f}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-zinc-500 text-xs block mb-1">Size</label>
              <input
                type="number"
                min={12}
                max={72}
                value={style.fontSize}
                disabled={loading}
                onChange={(e) =>
                  setStyle({ ...style, fontSize: Number(e.target.value) })
                }
                className="w-full bg-zinc-800 text-zinc-300 text-sm rounded px-2 py-1.5 border border-zinc-700 disabled:opacity-30"
              />
            </div>
            <div>
              <label className="text-zinc-500 text-xs block mb-1">Text Color</label>
              <input
                type="color"
                value={style.fontColor}
                disabled={loading}
                onChange={(e) =>
                  setStyle({ ...style, fontColor: e.target.value })
                }
                className="w-full h-8 rounded cursor-pointer bg-zinc-800 border border-zinc-700 disabled:opacity-30"
              />
            </div>
            <div>
              <label className="text-zinc-500 text-xs block mb-1">BG Color</label>
              <input
                type="color"
                value={style.bgColor}
                disabled={loading}
                onChange={(e) =>
                  setStyle({ ...style, bgColor: e.target.value })
                }
                className="w-full h-8 rounded cursor-pointer bg-zinc-800 border border-zinc-700 disabled:opacity-30"
              />
            </div>
            <div>
              <label className="text-zinc-500 text-xs block mb-1">
                BG Opacity
              </label>
              <input
                type="range"
                min={0}
                max={100}
                value={Math.round(style.bgOpacity * 100)}
                disabled={loading}
                onChange={(e) =>
                  setStyle({ ...style, bgOpacity: e.target.value / 100 })
                }
                className="w-full accent-emerald-500"
              />
            </div>
            <div>
              <label className="text-zinc-500 text-xs block mb-1">Position</label>
              <select
                value={style.position}
                disabled={loading}
                onChange={(e) =>
                  setStyle({ ...style, position: e.target.value })
                }
                className="w-full bg-zinc-800 text-zinc-300 text-sm rounded px-2 py-1.5 border border-zinc-700 disabled:opacity-30"
              >
                {STYLES.positions.map((p) => (
                  <option key={p.value} value={p.value}>
                    {p.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        <button
          onClick={handleSubmit}
          disabled={!file || loading}
          className="w-full bg-emerald-500 text-zinc-950 text-sm font-semibold py-2.5 rounded hover:bg-emerald-400 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? "Processing..." : "Generate Captions"}
        </button>

        {loading && (
          <div className="mt-4 flex flex-col items-center gap-2">
            <span className="inline-block w-5 h-5 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
            <p className="text-zinc-500 text-xs">
              Transcribing &amp; rendering captions...
            </p>
          </div>
        )}

        {error && (
          <p className="text-red-400 text-xs mt-4 text-center">{error}</p>
        )}

        {result && !loading && (
          <div className="mt-6 space-y-3">
            <video
              src={result.captioned_video_url || result.captioned_video}
              controls
              className="w-full rounded border border-zinc-700"
            />
            <div className="flex gap-2">
              <button
                onClick={() =>
                  handleDownload(
                    result.captioned_video_url || result.captioned_video,
                    "captioned_video.mp4"
                  )
                }
                className="flex-1 border border-emerald-500 text-emerald-400 text-sm py-2 rounded hover:bg-emerald-500 hover:text-zinc-950 transition-colors"
              >
                Download Video
              </button>
              {(result.subtitle_url || result.subtitle_file) && (
                <button
                  onClick={() =>
                    handleDownload(
                      result.subtitle_url || result.subtitle_file,
                      "captions.srt"
                    )
                  }
                  className="flex-1 border border-zinc-600 text-zinc-400 text-sm py-2 rounded hover:bg-zinc-800 transition-colors"
                >
                  Download SRT
                </button>
              )}
              {(result.audio_url || result.audio_file) && (
                <button
                  onClick={() =>
                    handleDownload(
                      result.audio_url || result.audio_file,
                      "audio.wav"
                    )
                  }
                  className="flex-1 border border-zinc-600 text-zinc-400 text-sm py-2 rounded hover:bg-zinc-800 transition-colors"
                >
                  Download Audio
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
