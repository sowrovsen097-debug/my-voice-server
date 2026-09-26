import gradio as gr
import asyncio
import edge_tts
import tempfile
import os
import re

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

async def generate_speech(text, voice, speed_pct, pitch_pct, emotion_level):
    if not text or not text.strip():
        return None

    formatted_text = inject_hyper_emotions(text, emotion_level)
    speed_str = f"{speed_pct:+d}%"
    pitch_str = f"{pitch_pct:+d}Hz"
    
    communicate = edge_tts.Communicate(formatted_text, voice, rate=speed_str, pitch=pitch_str)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
        output_path = tmp_file.name
        
    await communicate.save(output_path)
    return output_path

def process_tts(text, language, voice_choice, speed, pitch, emotion_intensity):
    voice_id = voice_choice.split(" | ")[0].strip()
    return asyncio.run(generate_speech(text, voice_id, speed, pitch, emotion_intensity))

def update_voice_options(lang):
    if lang == "English":
        return gr.Dropdown(
            choices=[
                "en-US-AnaNeural | Soft Emotional Female",
                "en-US-ChristopherNeural | Deep Dramatic Male",
                "en-US-JennyNeural | Natural Expressive Female",
                "en-US-GuyNeural | Narrative Voice Male",
                "en-GB-SoniaNeural | British Expressive Female",
                "en-GB-RyanNeural | British Deep Male"
            ],
            value="en-US-AnaNeural | Soft Emotional Female"
        )
    elif lang == "Bengali":
        return gr.Dropdown(
            choices=[
                "bn-BD-NabanitaNeural | Expressive Bengali Female",
                "bn-BD-PradeepNeural | Natural Bengali Male",
                "bn-IN-TanishaaNeural | Soft Indian Bengali Female"
            ],
            value="bn-BD-NabanitaNeural | Expressive Bengali Female"
        )
    else:
        return gr.Dropdown(
            choices=[
                "hi-IN-SwaraNeural | Deep Expressive Hindi Female",
                "hi-IN-MadhurNeural | Clear Narrative Hindi Male"
            ],
            value="hi-IN-SwaraNeural | Deep Expressive Hindi Female"
        )

with gr.Blocks(theme=gr.themes.Soft()) as app:
    gr.Markdown("# 🎙️ Hyper-Realistic Ultra-Emotional TTS Studio")
    
    with gr.Row():
        lang_dropdown = gr.Dropdown(
            choices=["English", "Bengali", "Hindi"], 
            value="English", 
            label="Language"
        )
        voice_dropdown = gr.Dropdown(
            choices=[
                "en-US-AnaNeural | Soft Emotional Female",
                "en-US-ChristopherNeural | Deep Dramatic Male",
                "en-US-JennyNeural | Natural Expressive Female",
                "en-US-GuyNeural | Narrative Voice Male",
                "en-GB-SoniaNeural | British Expressive Female",
                "en-GB-RyanNeural | British Deep Male"
            ],
            value="en-US-AnaNeural | Soft Emotional Female", 
            label="Voice Profile"
        )
    
    input_text = gr.Textbox(
        lines=5, 
        placeholder="Enter your script here... Use '...', '!', '-' to control timing, hesitation, and expression.", 
        label="Input Script"
    )
    
    with gr.Row():
        speed_slider = gr.Slider(minimum=-30, maximum=30, value=-5, step=1, label="Speed Rate (%)")
        pitch_slider = gr.Slider(minimum=-20, maximum=20, value=0, step=1, label="Pitch Modulation (Hz)")
        emotion_slider = gr.Slider(minimum=0, maximum=2, value=2, step=1, label="Emotion Intensity (0: Normal, 1: Deep, 2: Ultra)")
    
    generate_btn = gr.Button("✨ Generate Hyper-Realistic Voice", variant="primary")
    audio_output = gr.Audio(label="Generated Audio", type="filepath")

    lang_dropdown.change(fn=update_voice_options, inputs=lang_dropdown, outputs=voice_dropdown)
    
    generate_btn.click(
        fn=process_tts, 
        inputs=[input_text, lang_dropdown, voice_dropdown, speed_slider, pitch_slider, emotion_slider], 
        outputs=audio_output
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    app.launch(server_name="0.0.0.0", server_port=port)
