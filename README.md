# 🎬 Clipmaker

AI-powered tool to turn YouTube videos into viral clips automatically.

## ✨ Features

- 🤖 **AI Analysis** - Gemini 2.5 Flash finds viral moments
- ✂️ **Auto Clipping** - Cuts specific segments perfectly
- 📱 **Vertical Format** - 9:16 for TikTok/Shorts/Reels with face tracking
- 📥 **Multiple Sources** - YouTube URL or file upload
- ⚡ **Fast** - Compressed analysis for long videos
- 💰 **Free** - Just needs a Gemini API key

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Get API Key (Free)

Get your Gemini API key: https://aistudio.google.com/app/apikey

### 3. Configure

```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### 4. Run

```bash
streamlit run clipper_ui.py
```

Open http://localhost:8501 in your browser!

## 📖 How to Use

1. **Enter API Key** - Paste your Gemini API key in the sidebar
2. **Choose Video** - Upload a file OR paste YouTube URL
3. **Select Format** - Horizontal (16:9) or Vertical (9:16)
4. **Generate** - Click "Generate Viral Clips"
5. **Download** - Save your clips!

## 🎯 Output

- **Horizontal clips** - Perfect for YouTube
- **Vertical clips** - Auto-cropped with face tracking for TikTok/Shorts/Reels
- **Smart analysis** - AI finds the most engaging moments
- **High quality** - Clips from original video quality

## 🛠️ Requirements

- Python 3.9+
- FFmpeg (install: `brew install ffmpeg` on macOS)
- Gemini API key (free tier available)

## 💡 Tips

- **Long videos?** - Automatically compressed for analysis
- **Face in frame?** - Vertical clips auto-center on faces
- **Multiple clips?** - Adjust slider (1-10 clips)

## 📄 License

MIT - Use it however you want!

---

Built with Gemini AI + MoviePy + Streamlit
