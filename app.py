import gradio as gr
import asyncio
import edge_tts
from kokoro_onnx import Kokoro
import soundfile as sf
import tempfile
import os
import urllib.request
import re

MODEL_URL = "https://github.com/thebloke/kokoro-onnx-models/releases/download/v0.19/kokoro-v0_19.onnx"
VOICES_URL = "https://github.com/thebloke/kokoro-onnx-models/releases/download/v0.19/voices.bin"

MODEL_FILE = "kokoro-v0_19.onnx"
VOICES_FILE = "voices.bin"

def ensure_models():
    if not os.path.exists(MODEL_FILE):
        print("Downloading Kokoro ONNX Model...")
        urllib.request.urlretrieve(MODEL_URL, MODEL_FILE)
    if not os.path.exists(VOICES_FILE):
        print("Downloading Kokoro Voices Bin...")
        urllib.request.urlretrieve(VOICES_URL, VOICES_FILE)

ensure_models()
kokoro = Kokoro(MODEL_FILE, VOICES_FILE)

def inject_hyper_emotions(text, emotion_level):
    if not text:
        return ""
    
    text = text.strip()
    
    if emotion_level == 2:
        text = re.sub(r'(\!+)', r'! ... ', text)
        text = re.sub(r'(\?+)', r'? ... ', text)
        text = re.sub(r'(\.+)', r'... ', text)
        text = re.sub(r'(\,)', r', ', text)
        text = re.sub(r'(\-)', r' - ', text)
    elif emotion_level == 1:
        text = re.sub(r'(\!+)', r'! .. ', text)
        text = re.sub(r'(\?+)', r'? .. ', text)
        text = re.sub(r'(\.+)', r'.. ', text)
        text = re.sub(r'(\,)', r', ', text)
    
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

async def generate_edge_tts(text, voice, speed_pct):
    speed_str = f"{speed_pct:+d}%"
    communicate = edge_tts.Communicate(text, voice, rate=speed_str)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
        output_path = tmp_file.name
        
    await communicate.save(output_path)
    return output_path

def generate_voice(text, language, voice_choice, speed, emotion_intensity):
    if not text or not text.strip():
        return None
    
    voice_style = voice_choice.split(" ")[0].strip()
    enhanced_text = inject_hyper_emotions(text, emotion_intensity)
    
    if language == "Bengali":
        edge_voice = "bn-BD-NabanitaNeural" if "Nabanita" in voice_choice else "bn-BD-PradeepNeural"
        return asyncio.run(generate_edge_tts(enhanced_text, edge_voice, speed))
    else:
        speed_factor = (1.0 + (speed / 100.0)) * (1.0 - (emotion_intensity * 0.06))
        lang_code = "en-us" if language == "English" else "hi"
        
        samples, sample_rate = kokoro.create(
            enhanced_text, 
            voice=voice_style, 
            speed=speed_factor, 
            lang=lang_code
        )
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            output_path = tmp_file.name
            sf.write(output_path, samples, sample_rate)
            
        return output_path

def update_voice_options(lang):
    if lang == "English":
        return gr.Dropdown(
            choices=[
                "af_bella | Ultra Emotional Female", 
                "am_adam | Deep Cinematic Male", 
                "af_sarah | Dramatic Narrative Female", 
                "af_nicole | Soft Expressive Female",
                "am_michael | Natural Dialogue Male",
                "bf_emma | Expressive British Female"
            ], 
            value="af_bella | Ultra Emotional Female"
        )
    elif lang == "Hindi":
        return gr.Dropdown(
            choices=[
                "hf_alpha | Expressive Hindi Female", 
                "hm_omega | Dramatic Hindi Male"
            ], 
            value="hf_alpha | Expressive Hindi Female"
        )
    else:
        return gr.Dropdown(
            choices=[
                "bn-BD-NabanitaNeural (Female)", 
                "bn-BD-PradeepNeural (Male)"
            ], 
            value="bn-BD-NabanitaNeural (Female)"
        )

with gr.Blocks(theme=gr.themes.Soft()) as app:
    gr.Markdown("# 🎙️ ElevenLabs-Level Ultra-Emotional TTS Studio")
    
    with gr.Row():
        lang_dropdown = gr.Dropdown(choices=["Bengali", "English", "Hindi"], value="English", label="Language")
        voice_dropdown = gr.Dropdown(
            choices=[
                "af_bella | Ultra Emotional Female", 
                "am_adam | Deep Cinematic Male", 
                "af_sarah | Dramatic Narrative Female", 
                "af_nicole | Soft Expressive Female",
                "am_michael | Natural Dialogue Male",
                "bf_emma | Expressive British Female"
            ], 
            value="af_bella | Ultra Emotional Female", 
            label="Voice Profile"
        )
    
    input_text = gr.Textbox(lines=5, placeholder="Enter your script with punctuation like '...', '!', ',' to shape emotions...", label="Input Script")
    
    with gr.Row():
        speed_slider = gr.Slider(minimum=-30, maximum=30, value=-8, step=1, label="Speed Rate (%)")
        emotion_slider = gr.Slider(minimum=0, maximum=2, value=2, step=1, label="Emotion Intensity (0: Normal, 1: Deep, 2: Ultra)")
    
    generate_btn = gr.Button("✨ Generate Hyper-Realistic Voice", variant="primary")
    audio_output = gr.Audio(label="Generated Audio", type="filepath")

    lang_dropdown.change(fn=update_voice_options, inputs=lang_dropdown, outputs=voice_dropdown)
    generate_btn.click(
        fn=generate_voice, 
        inputs=[input_text, lang_dropdown, voice_dropdown, speed_slider, emotion_slider], 
        outputs=audio_output
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    app.launch(server_name="0.0.0.0", server_port=port)
