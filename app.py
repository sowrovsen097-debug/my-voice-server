import gradio as gr
import asyncio
import edge_tts
from kokoro_onnx import Kokoro
import soundfile as sf
import tempfile
import os
import urllib.request

# Model files URL
MODEL_URL = "https://github.com/thebloke/kokoro-onnx-models/releases/download/v0.19/kokoro-v0_19.onnx"
VOICES_URL = "https://github.com/thebloke/kokoro-onnx-models/releases/download/v0.19/voices.bin"

MODEL_FILE = "kokoro-v0_19.onnx"
VOICES_FILE = "voices.bin"

# Auto Download Kokoro Models if not present
def download_file(url, destination):
    if not os.path.exists(destination):
        print(f"Downloading {destination}...")
        urllib.request.urlretrieve(url, destination)
        print(f"Downloaded {destination} successfully.")

try:
    download_file(MODEL_URL, MODEL_FILE)
    download_file(VOICES_URL, VOICES_FILE)
    kokoro = Kokoro(MODEL_FILE, VOICES_FILE)
except Exception as e:
    print(f"Kokoro initialization error: {e}")
    kokoro = None

# Async function for Edge-TTS (Bengali)
async def generate_edge_tts(text, voice, speed_pct):
    speed_str = f"{speed_pct:+d}%"
    communicate = edge_tts.Communicate(text, voice, rate=speed_str)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
        output_path = tmp_file.name
        
    await communicate.save(output_path)
    return output_path

# Main Generation Function
def generate_voice(text, language, voice_choice, speed):
    if not text or not text.strip():
        return None
    
    # Bengali using Edge-TTS
    if language == "Bengali":
        edge_voice = "bn-BD-NabanitaNeural" if "Nabanita" in voice_choice else "bn-BD-PradeepNeural"
        return asyncio.run(generate_edge_tts(text, edge_voice, speed))

    # English & Hindi using Kokoro-TTS
    else:
        if kokoro is None:
            # Fallback to Edge-TTS if Kokoro fails
            fallback_voice = "en-US-AvaNeural" if language == "English" else "hi-IN-SwaraNeural"
            return asyncio.run(generate_edge_tts(text, fallback_voice, speed))
        
        try:
            speed_factor = 1.0 + (speed / 100.0)
            voice_style = voice_choice.split(" ")[0]
            
            samples, sample_rate = kokoro.create(
                text, 
                voice=voice_style, 
                speed=speed_factor, 
                lang="en-us" if language == "English" else "hi"
            )
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
                output_path = tmp_file.name
                sf.write(output_path, samples, sample_rate)
                
            return output_path
        except Exception as e:
            print(f"Error in Kokoro: {e}")
            fallback_voice = "en-US-AvaNeural" if language == "English" else "hi-IN-SwaraNeural"
            return asyncio.run(generate_edge_tts(text, fallback_voice, speed))

# Dynamic Voice Options
def update_voice_options(lang):
    if lang == "English":
        return gr.Dropdown(choices=["af_sarah (Female)", "am_adam (Male)", "bf_emma (British Female)"], value="af_sarah (Female)")
    elif lang == "Hindi":
        return gr.Dropdown(choices=["hf_alpha (Female)", "hm_omega (Male)"], value="hf_alpha (Female)")
    else:
        return gr.Dropdown(choices=["bn-BD-NabanitaNeural (Female)", "bn-BD-PradeepNeural (Male)"], value="bn-BD-NabanitaNeural (Female)")

# Gradio Interface
with gr.Blocks(theme=gr.themes.Soft()) as app:
    gr.Markdown("# 🎙️ Multi-Engine AI Voice Studio")
    
    with gr.Row():
        lang_dropdown = gr.Dropdown(choices=["Bengali", "English", "Hindi"], value="Bengali", label="Language / ভাষা")
        voice_dropdown = gr.Dropdown(choices=["bn-BD-NabanitaNeural (Female)", "bn-BD-PradeepNeural (Male)"], value="bn-BD-NabanitaNeural (Female)", label="Voice Accent")
    
    input_text = gr.Textbox(lines=4, placeholder="এখানে আপনার টেক্সট পেস্ট করুন...", label="Input Text")
    speed_slider = gr.Slider(minimum=-30, maximum=30, value=-6, step=1, label="Speed Adjustment (%)")
    
    generate_btn = gr.Button("✨ Generate Real Voice", variant="primary")
    audio_output = gr.Audio(label="Generated Audio", type="filepath")

    lang_dropdown.change(fn=update_voice_options, inputs=lang_dropdown, outputs=voice_dropdown)
    generate_btn.click(fn=generate_voice, inputs=[input_text, lang_dropdown, voice_dropdown, speed_slider], outputs=audio_output)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    app.launch(server_name="0.0.0.0", server_port=port)
