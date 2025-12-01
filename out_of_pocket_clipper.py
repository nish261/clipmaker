#!/usr/bin/env python3
"""
Out-of-Pocket Clipper - Automated Viral Content Generator
Workflow: YouTube -> Gemini Analysis -> Canva Template -> Viral Clips
"""

import os
import json
import time
import logging
from pathlib import Path
from typing import List, Dict
from dotenv import load_dotenv

import yt_dlp
import google.generativeai as genai
import requests
from moviepy import VideoFileClip

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class ContentIngestor:
    """Downloads YouTube videos using yt-dlp"""

    def __init__(self, output_dir: str = "temp"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def download_video(self, url: str) -> str:
        """
        Downloads a YouTube video in 1080p MP4 format

        Args:
            url: YouTube video URL

        Returns:
            Path to downloaded video file
        """
        logger.info(f"Starting download: {url}")

        output_path = self.output_dir / "raw_video.mp4"

        ydl_opts = {
            'format': 'bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4][height<=1080]',
            'outtmpl': str(output_path),
            'quiet': False,
            'no_warnings': False,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            logger.info(f"Download complete: {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"Download failed: {e}")
            raise


class ViralBrain:
    """Uses Gemini AI to analyze videos and identify viral moments"""

    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-pro-latest')

    def upload_to_gemini(self, file_path: str):
        """
        Uploads video to Gemini and waits for processing

        Args:
            file_path: Path to video file

        Returns:
            Gemini File object ready for analysis
        """
        logger.info(f"Uploading to Gemini: {file_path}")

        file = genai.upload_file(path=file_path)
        logger.info(f"File uploaded: {file.name}")

        # Wait for file to be processed
        while file.state.name == "PROCESSING":
            logger.info("Waiting for Gemini to process video...")
            time.sleep(2)
            file = genai.get_file(file.name)

        if file.state.name == "FAILED":
            raise ValueError(f"Video processing failed: {file.state.name}")

        logger.info("Video processing complete")
        return file

    def find_viral_clips(self, file_handle, num_clips: int = 3) -> List[Dict]:
        """
        Analyzes video to find viral 'out of pocket' moments

        Args:
            file_handle: Gemini File object
            num_clips: Number of clips to identify

        Returns:
            List of clip dictionaries with start, end, summary, virality_score
        """
        logger.info(f"Analyzing video for {num_clips} viral moments...")

        prompt = f"""
You are a viral content editor analyzing this video. Identify the {num_clips} MOST "out of pocket",
wild, unexpected, or highly viral segments from this video.

Requirements:
- Each clip should be 15-60 seconds long
- Focus on moments that are shocking, funny, controversial, or highly engaging
- Prioritize moments with strong emotional reactions or surprising content

Return ONLY valid JSON in this exact format (no markdown, no explanation):
[
  {{
    "start": "00:04:12",
    "end": "00:05:00",
    "summary": "Brief description of why this moment is viral-worthy",
    "virality_score": 8
  }}
]

Use HH:MM:SS format for timestamps. Virality score is 1-10.
"""

        try:
            response = self.model.generate_content([file_handle, prompt])
            logger.info("Gemini analysis complete")

            # Parse JSON response
            response_text = response.text.strip()

            # Remove markdown code blocks if present
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]

            clips = json.loads(response_text)

            logger.info(f"Found {len(clips)} viral moments")
            for i, clip in enumerate(clips, 1):
                logger.info(f"Clip {i}: {clip['start']} - {clip['end']} (Score: {clip['virality_score']}/10)")
                logger.info(f"  → {clip['summary']}")

            return clips

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            raise


class ClipProcessor:
    """Handles local video trimming using MoviePy"""

    def __init__(self, output_dir: str = "temp"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    @staticmethod
    def timestamp_to_seconds(timestamp: str) -> float:
        """Converts HH:MM:SS to seconds"""
        parts = timestamp.split(':')
        if len(parts) == 3:
            h, m, s = parts
            return int(h) * 3600 + int(m) * 60 + float(s)
        elif len(parts) == 2:
            m, s = parts
            return int(m) * 60 + float(s)
        else:
            return float(parts[0])

    def slice_video(self, raw_path: str, start_time: str, end_time: str, clip_index: int) -> str:
        """
        Cuts a specific segment from the video

        Args:
            raw_path: Path to source video
            start_time: Start timestamp (HH:MM:SS)
            end_time: End timestamp (HH:MM:SS)
            clip_index: Index for output filename

        Returns:
            Path to clipped video file
        """
        logger.info(f"Cutting clip {clip_index}: {start_time} -> {end_time}")

        start_sec = self.timestamp_to_seconds(start_time)
        end_sec = self.timestamp_to_seconds(end_time)

        output_path = self.output_dir / f"clip_{clip_index}.mp4"

        try:
            video = VideoFileClip(raw_path)
            clip = video.subclip(start_sec, end_sec)
            clip.write_videofile(
                str(output_path),
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                logger=None  # Suppress moviepy logs
            )
            video.close()
            clip.close()

            logger.info(f"Clip saved: {output_path}")
            return str(output_path)

        except Exception as e:
            logger.error(f"Clip processing failed: {e}")
            raise


class CanvaFactory:
    """Handles Canva API integration for template-based video generation"""

    BASE_URL = "https://api.canva.com/rest/v1"

    def __init__(self, access_token: str, brand_template_id: str):
        self.access_token = access_token
        self.brand_template_id = brand_template_id
        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

    def upload_asset(self, clip_path: str) -> str:
        """
        Uploads video clip to Canva as an asset

        Args:
            clip_path: Path to video file

        Returns:
            Canva asset ID
        """
        logger.info(f"Uploading to Canva: {clip_path}")

        url = f"{self.BASE_URL}/assets"

        with open(clip_path, 'rb') as f:
            files = {
                'asset': (Path(clip_path).name, f, 'video/mp4')
            }
            headers_upload = {
                "Authorization": f"Bearer {self.access_token}"
            }

            try:
                response = requests.post(url, headers=headers_upload, files=files)
                response.raise_for_status()

                asset_data = response.json()
                asset_id = asset_data['asset']['id']

                logger.info(f"Asset uploaded: {asset_id}")
                return asset_id

            except requests.exceptions.RequestException as e:
                logger.error(f"Asset upload failed: {e}")
                if hasattr(e.response, 'text'):
                    logger.error(f"Response: {e.response.text}")
                raise

    def generate_from_template(self, asset_id: str, summary: str = "") -> str:
        """
        Creates a design from brand template using autofill

        Args:
            asset_id: Canva asset ID
            summary: Optional text to add to template

        Returns:
            Design ID
        """
        logger.info(f"Generating design from template: {self.brand_template_id}")

        url = f"{self.BASE_URL}/autofills"

        payload = {
            "brand_template_id": self.brand_template_id,
            "data": {
                "video_placeholder_1": {
                    "type": "video",
                    "asset_id": asset_id
                }
            }
        }

        # Add text if summary provided
        if summary:
            payload["data"]["text_placeholder_1"] = {
                "type": "text",
                "text": summary
            }

        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()

            data = response.json()
            design_id = data['design']['id']

            logger.info(f"Design created: {design_id}")
            return design_id

        except requests.exceptions.RequestException as e:
            logger.error(f"Design creation failed: {e}")
            if hasattr(e.response, 'text'):
                logger.error(f"Response: {e.response.text}")
            raise

    def export_video(self, design_id: str, output_dir: str = "output") -> str:
        """
        Exports design as MP4 video and downloads it

        Args:
            design_id: Canva design ID
            output_dir: Directory to save exported video

        Returns:
            Path to downloaded video
        """
        logger.info(f"Exporting design: {design_id}")

        # Start export
        url = f"{self.BASE_URL}/exports"
        payload = {
            "design_id": design_id,
            "format": "mp4",
            "quality": "1080p"
        }

        try:
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()

            export_data = response.json()
            job_id = export_data['job']['id']

            logger.info(f"Export job started: {job_id}")

            # Poll for completion
            status_url = f"{self.BASE_URL}/exports/{job_id}"
            max_attempts = 60
            attempt = 0

            while attempt < max_attempts:
                time.sleep(3)
                attempt += 1

                status_response = requests.get(status_url, headers=self.headers)
                status_response.raise_for_status()

                status_data = status_response.json()
                status = status_data['job']['status']

                logger.info(f"Export status: {status} (attempt {attempt}/{max_attempts})")

                if status == 'success':
                    download_url = status_data['job']['result']['url']

                    # Download the video
                    output_path = Path(output_dir)
                    output_path.mkdir(exist_ok=True)

                    filename = output_path / f"canva_video_{design_id}.mp4"

                    logger.info(f"Downloading video from: {download_url}")
                    video_response = requests.get(download_url)
                    video_response.raise_for_status()

                    with open(filename, 'wb') as f:
                        f.write(video_response.content)

                    logger.info(f"Video saved: {filename}")
                    return str(filename)

                elif status == 'failed':
                    raise Exception(f"Export failed: {status_data}")

            raise TimeoutError("Export took too long (timeout after 3 minutes)")

        except requests.exceptions.RequestException as e:
            logger.error(f"Export failed: {e}")
            if hasattr(e.response, 'text'):
                logger.error(f"Response: {e.response.text}")
            raise


def main(youtube_url: str, num_clips: int = 3):
    """
    Main execution flow

    Args:
        youtube_url: YouTube video URL to process
        num_clips: Number of viral clips to generate (default: 3)
    """
    logger.info("=" * 60)
    logger.info("OUT-OF-POCKET CLIPPER - Starting Pipeline")
    logger.info("=" * 60)

    # Load configuration
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    canva_access_token = os.getenv("CANVA_ACCESS_TOKEN")
    canva_template_id = os.getenv("CANVA_BRAND_TEMPLATE_ID")

    if not all([gemini_api_key, canva_access_token, canva_template_id]):
        raise ValueError("Missing required environment variables. Check your .env file.")

    # Initialize components
    ingestor = ContentIngestor()
    brain = ViralBrain(gemini_api_key)
    processor = ClipProcessor()
    factory = CanvaFactory(canva_access_token, canva_template_id)

    try:
        # 1. Download video
        logger.info("\n[STEP 1/4] Downloading video...")
        raw_video = ingestor.download_video(youtube_url)

        # 2. Analyze with Gemini
        logger.info("\n[STEP 2/4] Analyzing with Gemini AI...")
        gemini_file = brain.upload_to_gemini(raw_video)
        clips_data = brain.find_viral_clips(gemini_file, num_clips=num_clips)

        # 3. Process each clip
        logger.info(f"\n[STEP 3/4] Processing {len(clips_data)} clips...")
        output_videos = []

        for i, clip in enumerate(clips_data, 1):
            logger.info(f"\n--- Processing Clip {i}/{len(clips_data)} ---")

            # Cut locally
            local_clip = processor.slice_video(
                raw_video,
                clip['start'],
                clip['end'],
                i
            )

            # 4. Render in Canva
            logger.info(f"\n[STEP 4/{len(clips_data)}] Generating Canva video {i}...")
            asset_id = factory.upload_asset(local_clip)
            design_id = factory.generate_from_template(asset_id, clip['summary'])
            final_video = factory.export_video(design_id)

            output_videos.append({
                'path': final_video,
                'summary': clip['summary'],
                'virality_score': clip['virality_score']
            })

            logger.info(f"✅ Video {i} Complete: {final_video}")

        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("PIPELINE COMPLETE!")
        logger.info("=" * 60)
        logger.info(f"Generated {len(output_videos)} viral clips:")

        for i, video in enumerate(output_videos, 1):
            logger.info(f"\n{i}. {video['path']}")
            logger.info(f"   Score: {video['virality_score']}/10")
            logger.info(f"   Summary: {video['summary']}")

        return output_videos

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python out_of_pocket_clipper.py <youtube_url> [num_clips]")
        print("Example: python out_of_pocket_clipper.py 'https://www.youtube.com/watch?v=dQw4w9WgXcQ' 5")
        sys.exit(1)

    url = sys.argv[1]
    clips = int(sys.argv[2]) if len(sys.argv) > 2 else 3

    main(url, clips)
