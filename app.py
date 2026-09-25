import os, io, re, asyncio
import edge_tts
import gradio as gr
from pydub import AudioSegment

# বাংলা + ইংরেজি ভয়েস (neural)
VOICES = {
    "বাংলা – নারী (Nabanita, ঢাকা)":      "bn-BD-NabanitaNeural",
    "বাংলা – পুরুষ (Pradeep, ঢাকা)":      "bn-BD-PradeepNeural",
    "বাংলা – নারী (Tanishaa, কলকাতা)":    "bn-IN-TanishaaNeural",
    "বাংলা – পুরুষ (Bashkar, কলকাতা)":    "bn-IN-BashkarNeural",
    "English – Female (Aria)":            "en-US-AriaNeural",
    "English – Male (Guy)":               "en-US-GuyNeural",
}


def split_sentences(text: str):
    # বাংলা দাঁড়ি (।), ইংরেজি ., !, ? — সবখানে ভাঙবে
    parts = re.split(r'(?<=[।\.!\?])\s+', text.strip())
    return [p.strip() for p in parts if p.strip()]


async def synth(text, voice, rate, pitch):
    communicate = edge_tts.Communicate(
        text, voice, rate=rate, pitch=pitch, volume="+0%"
    )
    buf = b""
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            buf += chunk["data"]
    return buf


async def generate(text, voice_name, rate_pct, pitch_hz, pause_ms, progress=gr.Progress()):
    if not text or not text.strip():
        raise gr.Error("টেক্সট লিখুন।")

    voice = VOICES[voice_name]
    rate = f"{int(rate_pct):+d}%"
    pitch = f"{int(pitch_hz):+d}Hz"

    sentences = split_sentences(text)
    gap = AudioSegment.silent(duration=int(pause_ms))

    combined = AudioSegment.empty()
    for i, s in enumerate(sentences):
        progress(i / max(len(sentences), 1), desc=f"বাক্য {i+1}/{len(sentences)}")
        data = await synth(s, voice, rate, pitch)
        seg = AudioSegment.from_file(io.BytesIO(data), format="mp3")
        combined += seg
        if i < len(sentences) - 1:
            combined += gap

    # ভলিউম নরমালাইজ — ElevenLabs-এর মতো সমান লাউডনেস
    combined = combined.normalize()

    out = io.BytesIO()
    combined.export(out, format="mp3", bitrate="192k")
    out.seek(0)
    return out


with gr.Blocks(title="Voice Studio – Neural") as demo:
    gr.Markdown("## 🎙️ Voice Studio — Neural AI (Tuned)")
    with gr.Row():
        voice_dd = gr.Dropdown(
            list(VOICES.keys()), value=list(VOICES.keys())[0], label="ভয়েস"
        )
    txt = gr.Textbox(lines=8, label="টেক্সট / স্ক্রিপ্ট")
    with gr.Row():
        rate_sl = gr.Slider(-30, 10, value=-10, step=1,
                            label="Speed (%)  (− = ধীর, সাবলীল)")
        pitch_sl = gr.Slider(-30, 30, value=0, step=1, label="Pitch (Hz)")
        pause_sl = gr.Slider(0, 900, value=350, step=25,
                             label="বাক্যের মাঝে বিরতি (ms)")
    btn = gr.Button("🔊 Generate", variant="primary")
    out_audio = gr.Audio(label="Output", type="filepath")
    btn.click(generate, [txt, voice_dd, rate_sl, pitch_sl, pause_sl], out_audio)


if __name__ == "__main__":
    demo.queue().launch(
        server_name="0.0.0.0",
        server_port=int(os.environ.get("PORT", 7860)),
)
