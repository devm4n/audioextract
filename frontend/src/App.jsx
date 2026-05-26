import axios from "axios";
import { useState } from "react";

export default function App() {
  const [file, setFile] = useState(null);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("");
  const [audioUrl, setAudioUrl] = useState(null);
  const apiUrl = import.meta.env.VITE_API_URL;

  const handleSubmit = async () => {
    const form = new FormData();
    form.append("video_file", file);
    try {
      setStatus("uploading");
      const response = await axios.post(`${apiUrl}/upload/`, form);
      const { id } = response.data;
      setStatus("processing");
      const interval = setInterval(async () => {
        const { data } = await axios.get(`${apiUrl}/status/${id}/`);
        if (data.status === "done") {
          clearInterval(interval);
          setStatus("done");
          setAudioUrl(data.audio_url);
        } else if (data.status === "failed") {
          setStatus("failed");
          clearInterval(interval);
        }
      }, 3000);
      return response.data;
    } catch (err) {
      setStatus("failed");
      setError(err.response?.data?.video_file?.[0] ?? "");
      return console.log(err.response?.data);
    }
  };

  const handleDownload = async (audioUrl, filename) => {
    const res = await fetch(audioUrl);
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename || "audio.mp3";
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="bg-zinc-950 min-h-screen flex items-center justify-center font-mono">
      <div className="w-full max-w-sm px-4">
        <h2 className="text-zinc-500 text-xl uppercase tracking-widest mb-6">
          audioextract
        </h2>

        <label className="block w-full border border-dashed border-zinc-700 rounded p-6 text-center cursor-pointer hover:border-emerald-500 transition-colors group mb-4">
          <span className="text-zinc-400 text-sm group-hover:text-emerald-400 transition-colors">
            {file ? file.name : "drop video or click to choose"}
          </span>
          <input
            type="file"
            className="hidden"
            onChange={(e) => setFile(e.target.files[0])}
          />
        </label>

        <button
          onClick={handleSubmit}
          disabled={!file}
          className="w-full bg-emerald-500 text-zinc-950 text-sm font-semibold py-2.5 rounded hover:bg-emerald-400 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
        >
          Process
        </button>

        {(status || error) && (
          <p className="text-zinc-500 text-xs mt-4">
            {status}
            {error && <span className="text-red-400 ml-1">{error}</span>}
          </p>
        )}

        {audioUrl && (
          <button
            onClick={() => handleDownload(audioUrl, "audio.mp3")}
            className="mt-3 w-full border border-emerald-500 text-emerald-400 text-sm py-2.5 rounded hover:bg-emerald-500 hover:text-zinc-950 transition-colors"
          >
            Download MP3
          </button>
        )}
      </div>
    </div>
  );
}
