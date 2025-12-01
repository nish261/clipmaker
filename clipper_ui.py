#!/usr/bin/env python3
"""
Streamlit UI for Out-of-Pocket Clipper
A beautiful interface for generating viral clips from YouTube videos
"""

import os
import sys
import streamlit as st
from pathlib import Path
from dotenv import load_dotenv, set_key
import time

# Load environment variables
load_dotenv()

# Page config
st.set_page_config(
    page_title="Out-of-Pocket Clipper",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        text-align: center;
        color: #666;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        font-weight: 600;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-size: 1.1rem;
    }
    .stButton>button:hover {
        opacity: 0.9;
    }
    .success-box {
        padding: 1rem;
        background: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 8px;
        color: #155724;
        margin: 1rem 0;
    }
    .error-box {
        padding: 1rem;
        background: #f8d7da;
        border: 1px solid #f5c6cb;
        border-radius: 8px;
        color: #721c24;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">🎬 Out-of-Pocket Clipper</h1>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">Turn YouTube videos into viral clips with AI</p>', unsafe_allow_html=True)

# Sidebar - Configuration
with st.sidebar:
    st.header("⚙️ Configuration")

    # API Keys Section
    with st.expander("🔑 API Keys", expanded=True):
        gemini_key = st.text_input(
            "Gemini API Key",
            value=os.getenv("GEMINI_API_KEY", ""),
            type="password",
            help="Get from: https://aistudio.google.com/app/apikey"
        )

        canva_token = st.text_input(
            "Canva Access Token",
            value=os.getenv("CANVA_ACCESS_TOKEN", ""),
            type="password",
            help="Get from: https://www.canva.com/developers/"
        )

        canva_template = st.text_input(
            "Canva Template ID",
            value=os.getenv("CANVA_BRAND_TEMPLATE_ID", ""),
            help="Your Canva brand template ID"
        )

        if st.button("💾 Save API Keys"):
            env_path = Path(".env")
            set_key(env_path, "GEMINI_API_KEY", gemini_key)
            set_key(env_path, "CANVA_ACCESS_TOKEN", canva_token)
            set_key(env_path, "CANVA_BRAND_TEMPLATE_ID", canva_template)
            st.success("✅ API keys saved to .env")
            time.sleep(1)
            st.rerun()

    # Quick Links
    st.markdown("---")
    st.markdown("### 📚 Quick Links")
    st.markdown("[📖 Documentation](https://github.com)")
    st.markdown("[🔑 Get Gemini API Key](https://aistudio.google.com/app/apikey)")
    st.markdown("[🎨 Canva Developers](https://www.canva.com/developers/)")

    # Status
    st.markdown("---")
    st.markdown("### 📊 Status")

    # Check if dependencies are ready
    deps_ready = all([
        os.path.exists("out_of_pocket_clipper.py"),
        gemini_key and len(gemini_key) > 10,
        canva_token and len(canva_token) > 10,
        canva_template and len(canva_template) > 3
    ])

    if deps_ready:
        st.success("✅ All configured")
    else:
        st.warning("⚠️ Configure API keys")

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    st.header("📺 YouTube Video")
    youtube_url = st.text_input(
        "YouTube URL",
        placeholder="https://www.youtube.com/watch?v=...",
        help="Paste the full YouTube video URL here"
    )

    # Show video preview if URL is provided
    if youtube_url and "youtube.com" in youtube_url:
        try:
            st.video(youtube_url)
        except:
            st.info("Preview will appear when video loads")

with col2:
    st.header("⚡ Settings")

    num_clips = st.slider(
        "Number of clips to generate",
        min_value=1,
        max_value=10,
        value=3,
        help="How many viral moments to extract"
    )

    st.info(f"Will generate **{num_clips}** clips")

# Generate button
st.markdown("---")

if not deps_ready:
    st.error("❌ Please configure your API keys in the sidebar first")
elif not youtube_url:
    st.info("👆 Enter a YouTube URL above to get started")
else:
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        if st.button("🚀 Generate Viral Clips", key="generate_btn"):

            # Create a placeholder for status updates
            status_container = st.container()

            with status_container:
                st.markdown("### 🎬 Processing...")

                progress_bar = st.progress(0)
                status_text = st.empty()

                try:
                    # Import the clipper
                    from out_of_pocket_clipper import (
                        ContentIngestor,
                        ViralBrain,
                        ClipProcessor,
                        CanvaFactory
                    )

                    # Initialize components
                    status_text.text("🔧 Initializing components...")
                    progress_bar.progress(5)

                    ingestor = ContentIngestor()
                    brain = ViralBrain(gemini_key)
                    processor = ClipProcessor()
                    factory = CanvaFactory(canva_token, canva_template)

                    # Step 1: Download
                    status_text.text("📥 Downloading video from YouTube...")
                    progress_bar.progress(10)

                    raw_video = ingestor.download_video(youtube_url)

                    status_text.text("✅ Video downloaded successfully!")
                    progress_bar.progress(30)

                    # Step 2: Analyze
                    status_text.text("🧠 Uploading to Gemini AI...")
                    progress_bar.progress(35)

                    gemini_file = brain.upload_to_gemini(raw_video)

                    status_text.text("🔍 Analyzing video for viral moments...")
                    progress_bar.progress(40)

                    clips_data = brain.find_viral_clips(gemini_file, num_clips=num_clips)

                    status_text.text(f"✅ Found {len(clips_data)} viral moments!")
                    progress_bar.progress(50)

                    # Step 3 & 4: Process each clip
                    output_videos = []

                    for i, clip in enumerate(clips_data, 1):
                        progress_pct = 50 + int((i / len(clips_data)) * 45)

                        # Cut locally
                        status_text.text(f"✂️ Cutting clip {i}/{len(clips_data)}...")
                        progress_bar.progress(progress_pct - 3)

                        local_clip = processor.slice_video(
                            raw_video,
                            clip['start'],
                            clip['end'],
                            i
                        )

                        # Upload to Canva
                        status_text.text(f"☁️ Uploading clip {i} to Canva...")
                        progress_bar.progress(progress_pct - 2)

                        asset_id = factory.upload_asset(local_clip)

                        # Generate from template
                        status_text.text(f"🎨 Applying brand template to clip {i}...")
                        progress_bar.progress(progress_pct - 1)

                        design_id = factory.generate_from_template(asset_id, clip['summary'])

                        # Export
                        status_text.text(f"🎬 Rendering final video {i}/{len(clips_data)}...")
                        progress_bar.progress(progress_pct)

                        final_video = factory.export_video(design_id)

                        output_videos.append({
                            'path': final_video,
                            'summary': clip['summary'],
                            'virality_score': clip['virality_score'],
                            'start': clip['start'],
                            'end': clip['end']
                        })

                    # Complete!
                    progress_bar.progress(100)
                    status_text.text("🎉 All clips generated successfully!")

                    # Display results
                    st.markdown("---")
                    st.markdown("## 🎬 Your Viral Clips")

                    for i, video in enumerate(output_videos, 1):
                        with st.expander(f"📹 Clip {i} - Score: {video['virality_score']}/10", expanded=True):
                            col_vid, col_info = st.columns([2, 1])

                            with col_vid:
                                # Display the video
                                if os.path.exists(video['path']):
                                    st.video(video['path'])

                                    # Download button
                                    with open(video['path'], 'rb') as f:
                                        st.download_button(
                                            label=f"⬇️ Download Clip {i}",
                                            data=f.read(),
                                            file_name=f"viral_clip_{i}.mp4",
                                            mime="video/mp4"
                                        )

                            with col_info:
                                st.markdown(f"**Timestamp:** `{video['start']} - {video['end']}`")
                                st.markdown(f"**Virality Score:** {video['virality_score']}/10")
                                st.markdown(f"**Summary:**")
                                st.write(video['summary'])

                    st.balloons()

                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    st.exception(e)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 2rem 0;'>
    <p>Built with ❤️ using Streamlit + Gemini AI + Canva API</p>
    <p style='font-size: 0.9rem;'>Need help? Check the README or documentation</p>
</div>
""", unsafe_allow_html=True)
