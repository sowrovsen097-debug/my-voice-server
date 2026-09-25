import os, io, re, asyncio, tempfile, time
import edge_tts
import gradio as gr
from pydub import AudioSegment

VOICES = {
    "বাংলা – নারী (Nabanita, ঢাকা)":   "bn-BD-NabanitaNeural",
    "বাংলা – পুরুষ (Pradeep, ঢাকা)":   "bn-BD-PradeepNeural",
    "বাংলা – নারী (Tanishaa, কলকাতা)": "bn-IN-TanishaaNeural",
    "বাংলা – পুরুষ (Bashkar, কলকাতা)": "bn-IN-BashkarNeural",
    "English – Female (Aria)":         "en-US-AriaNeural",
    "English – Male (Guy)":            "en-US-GuyNeural",
}


def split_sentences(text: str):
    parts = re.split(r'(?<=[।\.!\?])\s+', text.strip())
    return [p.strip() for p in parts if p.strip()]


async def synth_once(text, voice, rate, pitch):
    c = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch, volume="+0%")
    buf = b""
    async for ch in c.stream():
        if ch["type"] == "audio":
            buf += ch["data"]
    return buf


async def synth_retry(text, voice, rate, pitch, attempts=4):
    last = ""
    for i in range(attempts):
        try:
            data = await synth_once(text, voice, rate, pitch)
            if data:
                return data, ""
            last = "সার্ভার খালি রেসপন্স দিয়েছে"
        except Exception as e:
            last = f"{type(e).__name__}: {e}"
        await asyncio.sleep(0.8 * (i + 1))
    return None, last


async def generate(text, voice_name, rate_pct, pitch_hz, pause_ms, progress=gr.Progress()):
    if not text or not text.strip():
        raise gr.Error("টেক্সট লিখুন।")

    text = text.replace("\u200b", "").replace("\ufeff", "").strip()
    voice = VOICES[voice_name]
    rate = f"{int(rate_pct):+d}%"
    pitch = f"{int(pitch_hz):+d}Hz"

    sentences = split_sentences(text)
    if not sentences:
        raise gr.Error("বৈধ কোনো বাক্য পাওয়া যায়নি।")

    gap = AudioSegment.silent(duration=int(pause_ms))
    combined = AudioSegment.empty()
    ok, last_err = 0, ""

    for i, s in enumerate(sentences):
        progress((i + 1) / (len(sentences) + 1),
                 desc=f"বাক্য {i + 1}/{len(sentences)} তৈরি হচ্ছে...")
        data, err = await synth_retry(s, voice, rate, pitch)
        if data is None:
            last_err = err
            continue
        combined += AudioSegment.from_file(io.BytesIO(data), format="mp3")
        if i < len(sentences) - 1:
            combined += gap
        ok += 1

    if ok == 0:
        raise gr.Error(
            "কোনো বাক্যেরই অডিও পাওয়া যায়নি — মাইক্রোসফট সার্ভার সাময়িকভাবে ব্লক করেছে। "
            f"কারণ: {last_err} | একটু পরে আবার Generate চাপুন।"
        )

    combined = combined.normalize()
    out_path = os.path.join(tempfile.gettempdir(), f"voice_{int(time.time() * 1000)}.mp3")
    combined.export(out_path, format="mp3", bitrate="192k")
    return out_path


with gr.Blocks(title="Voice Studio – Neural") as demo:
    gr.Markdown("## 🎙️ Voice Studio — Neural AI (Tuned)")
    with gr.Row():
        voice_dd = gr.Dropdown(list(VOICES.keys()), value=list(VOICES.keys())[0], label="ভয়েস")
    txt = gr.Textbox(lines=8, label="টেক্সট / স্ক্রিপ্ট")
    with gr.Row():
        rate_sl = gr.Slider(-30, 10, value=-10, step=1, label="Speed (%)  (− = ধীর, সাবলীল)")
        pitch_sl = gr.Slider(-30, 30, value=0, step=1, label="Pitch (Hz)")
        pause_sl = gr.Slider(0, 900, value=350, step=25, label="বাক্যের মাঝে বিরতি (ms)")
    btn = gr.Button("🔊 Generate", variant="primary")
    out_audio = gr.Audio(label="Output", type="filepath")
    btn.click(generate, [txt, voice_dd, rate_sl, pitch_sl, pause_sl], out_audio)


if __name__ == "__main__":
    demo.queue().launch(
        server_name="0.0.0.0",
        server_port=int(os.environ.get("PORT", 7860)),
        )
