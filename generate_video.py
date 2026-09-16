#!/usr/bin/env python3
"""
Chinese Character Stroke Animation Video Generator

Generates MP4 videos showing stroke-by-stroke writing animation of Chinese characters,
matching the style of Chinese learning apps (ghost outline + progressive stroke reveal).

Usage:
    python generate_video.py "城市" "chéng shì" "city; town; urban area"
    python generate_video.py "学生" "xué shēng" "student" -o student.mp4
    python generate_video.py "爱" "ài" "love" --voice zh-CN-YunxiNeural
"""

import argparse
import asyncio
import json
import os
import subprocess
import sys
import tempfile


def check_dependencies():
    errors = []
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        errors.append("ffmpeg not found in PATH")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        errors.append("playwright not installed (pip install playwright)")
    if errors:
        for e in errors:
            print(f"  Missing: {e}")
        sys.exit(1)


def generate_html(characters, pinyin, meaning):
    num = len(characters)
    if num == 1:
        char_size, gap, font_size = 280, 0, 48
    elif num == 2:
        char_size, gap, font_size = 200, 50, 42
    elif num <= 4:
        char_size, gap, font_size = 150, 30, 36
    else:
        char_size, gap, font_size = 120, 20, 32

    chars_json = json.dumps(characters)
    full_word = "".join(characters)

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500&display=swap" rel="stylesheet">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  html, body {{
    width: 576px; height: 1024px;
    background: #FFFFFF;
  }}
  body {{
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    font-family: 'Noto Sans SC', 'Microsoft YaHei', sans-serif;
    overflow: hidden;
  }}
  .pinyin {{
    font-size: {font_size}px; color: #444;
    margin-bottom: 40px; letter-spacing: 6px; font-weight: 300;
  }}
  .characters {{
    display: flex; gap: {gap}px;
    align-items: center; justify-content: center;
  }}
  .char-container {{ width: {char_size}px; height: {char_size}px; }}
  .bottom-section {{
    margin-top: 70px; text-align: center;
    opacity: 0; transition: opacity 0.8s ease-in;
  }}
  .bottom-section.show {{ opacity: 1; }}
  .bottom-chars {{ font-size: 32px; color: #333; margin-bottom: 10px; }}
  .meaning {{ font-size: 20px; color: #777; font-weight: 300; }}
</style>
<script src="https://cdn.jsdelivr.net/npm/hanzi-writer@3.5/dist/hanzi-writer.min.js"></script>
</head>
<body>
  <div class="pinyin">{pinyin}</div>
  <div class="characters" id="chars"></div>
  <div class="bottom-section" id="bottomSection">
    <div class="bottom-chars">{full_word}</div>
    <div class="meaning">{meaning}</div>
  </div>
  <script>
    const CHARS = {chars_json};
    const SIZE = {char_size};
    const charsDiv = document.getElementById('chars');
    const writers = [];
    let loaded = 0;

    CHARS.forEach((c, i) => {{
      const el = document.createElement('div');
      el.className = 'char-container';
      el.id = 'c' + i;
      charsDiv.appendChild(el);
      writers.push(HanziWriter.create('c' + i, c, {{
        width: SIZE, height: SIZE,
        showOutline: true, showCharacter: false,
        strokeAnimationSpeed: 1, delayBetweenStrokes: 400,
        padding: 5, strokeColor: '#222', outlineColor: '#DDD',
        onLoadCharDataSuccess: () => {{ if (++loaded === CHARS.length) window.__dataLoaded = true; }},
        onLoadCharDataError: () => {{ loaded++; console.error('Failed to load: ' + c); }}
      }}));
    }});

    window.__animationDone = false;
    window.__dataLoaded = false;

    async function run() {{
      while (!window.__dataLoaded) await new Promise(r => setTimeout(r, 100));
      await new Promise(r => setTimeout(r, 1200));

      for (let i = 0; i < writers.length; i++) {{
        await new Promise(resolve => writers[i].animateCharacter({{ onComplete: resolve }}));
        if (i < writers.length - 1) await new Promise(r => setTimeout(r, 800));
      }}

      await new Promise(r => setTimeout(r, 800));
      document.getElementById('bottomSection').classList.add('show');
      await new Promise(r => setTimeout(r, 2500));
      window.__animationDone = true;
    }}

    setTimeout(run, 500);
  </script>
</body>
</html>"""


async def generate_tts(text, output_path, voice="zh-CN-XiaoxiaoNeural"):
    import edge_tts
    await edge_tts.Communicate(text, voice).save(output_path)


def record_animation(html_content, video_dir):
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(
            viewport={"width": 576, "height": 1024},
            record_video_dir=video_dir,
            record_video_size={"width": 576, "height": 1024},
        )
        page = ctx.new_page()
        page.set_content(html_content, wait_until="domcontentloaded")

        print("  Waiting for character data to load...")
        page.wait_for_function("window.__dataLoaded === true", timeout=30000)
        print("  Animating strokes...")
        page.wait_for_function("window.__animationDone === true", timeout=120000)
        page.wait_for_timeout(300)

        vid = page.video.path()
        ctx.close()
        browser.close()
        return vid


def compile_final(raw_video, audio_path, output_path, audio_delay_ms=1500):
    if audio_path and os.path.exists(audio_path):
        cmd = [
            "ffmpeg", "-y",
            "-i", raw_video,
            "-i", audio_path,
            "-filter_complex",
            f"[1:a]adelay={audio_delay_ms}|{audio_delay_ms},apad[a]",
            "-map", "0:v", "-map", "[a]",
            "-c:v", "libx264", "-preset", "medium", "-crf", "18",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-b:a", "128k",
            "-shortest", "-movflags", "+faststart",
            output_path,
        ]
    else:
        cmd = [
            "ffmpeg", "-y",
            "-i", raw_video,
            "-c:v", "libx264", "-preset", "medium", "-crf", "18",
            "-pix_fmt", "yuv420p", "-an",
            "-movflags", "+faststart",
            output_path,
        ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ffmpeg error: {result.stderr[-500:]}")
        return False
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Generate Chinese character stroke animation videos",
        epilog='Example: python generate_video.py "城市" "chéng shì" "city; town"',
    )
    parser.add_argument("characters", help="Chinese characters (e.g. '城市')")
    parser.add_argument("pinyin", help="Pinyin with tone marks (e.g. 'chéng shì')")
    parser.add_argument("meaning", help="English meaning (e.g. 'city; town')")
    parser.add_argument("-o", "--output", help="Output MP4 path")
    parser.add_argument("--voice", default="zh-CN-XiaoxiaoNeural", help="TTS voice")
    parser.add_argument("--no-audio", action="store_true", help="Skip audio")

    args = parser.parse_args()
    check_dependencies()

    chars = list(args.characters)
    out = args.output or os.path.join(os.getcwd(), f"{''.join(chars)}_stroke.mp4")
    out = os.path.abspath(out)

    print(f"Characters : {''.join(chars)}")
    print(f"Pinyin     : {args.pinyin}")
    print(f"Meaning    : {args.meaning}")
    print(f"Output     : {out}")
    print()

    with tempfile.TemporaryDirectory() as tmp:
        html_content = generate_html(chars, args.pinyin, args.meaning)

        audio_path = None
        if not args.no_audio:
            print("[1/3] Generating pronunciation audio...")
            try:
                audio_path = os.path.join(tmp, "audio.mp3")
                asyncio.run(generate_tts(args.characters, audio_path, args.voice))
                print("  Done")
            except Exception as e:
                print(f"  Warning: TTS failed ({e}), continuing without audio")
                audio_path = None
        else:
            print("[1/3] Skipping audio")

        print("[2/3] Recording stroke animation...")
        vdir = os.path.join(tmp, "vid")
        os.makedirs(vdir)
        raw = record_animation(html_content, vdir)
        print("  Done")

        print("[3/3] Compiling final video...")
        if compile_final(raw, audio_path, out):
            kb = os.path.getsize(out) / 1024
            print(f"\nVideo saved: {out}  ({kb:.0f} KB)")
        else:
            print("\nFailed to compile video")
            sys.exit(1)


if __name__ == "__main__":
    main()
