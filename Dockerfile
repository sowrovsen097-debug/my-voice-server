FROM python:3.10-slim

# Install system dependencies & wget
RUN apt-get update && apt-get install -y \
    ffmpeg \
    espeak-ng \
    build-essential \
    wget \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Pre-download Kokoro ONNX model and voices during build
RUN wget -q https://github.com/thebloke/kokoro-onnx-models/releases/download/v0.19/kokoro-v0_19.onnx -O kokoro-v0_19.onnx
RUN wget -q https://github.com/thebloke/kokoro-onnx-models/releases/download/v0.19/voices.bin -O voices.bin

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 7860

CMD ["python", "app.py"]
