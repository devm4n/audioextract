import axios from "axios";
import { useState } from "react";

export default function App() {
  const [file, setFile] = useState(null);
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
      const intervel = setInterval(async () => {
        const { data } = await axios.get(`${apiUrl}/status/${id}/`);
        if (data.status == "done") {
          clearInterval(intervel);
          setStatus("done");
          setAudioUrl(data.audio_url);
        }
      }, 3000);
      return response.data;
    } catch (err) {
      return console.log(err.response.data);
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
    <>
      <div>
        <input type="file" onChange={(e) => setFile(e.target.files[0])}></input>
        <button onClick={handleSubmit} disabled={!file}>
          Process
        </button>
        <p>{status}</p>
        {audioUrl && (
          <button onClick={() => handleDownload(audioUrl, "audio.mp3")}>
            Download MP3
          </button>
        )}
      </div>
    </>
  );
}
