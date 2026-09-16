# Chinese Character Stroke Animation Video Generator

Generate MP4 videos showing stroke-by-stroke writing animation of Chinese characters, with pronunciation audio. Videos are in 576x1024 portrait format (TikTok/Reels/Shorts ready).

## Example Output

Each video shows:
1. Pinyin pronunciation text at the top
2. Ghost outlines of the characters (light gray)
3. Strokes drawn one by one in correct writing order (black)
4. English meaning revealed at the end
5. Audio pronunciation of the word

---

## Quick Start (For AI Assistants - Claude Code / Codex / GPT)

If you are an AI assistant, run the following command to generate a video. **No other steps needed** - just run the command directly.

### Input Format

```
python generate_video.py "<chinese_characters>" "<pinyin_with_tones>" "<english_meaning>"
```

### The 3 required inputs:

1. **Chinese characters** - The word in Chinese (e.g. `"城市"`, `"猫"`, `"学生"`)
2. **Pinyin with tone marks** - Romanized pronunciation (e.g. `"chéng shì"`, `"māo"`, `"xué shēng"`)
3. **English meaning** - Translation (e.g. `"city; town"`, `"cat"`, `"student"`)

### Copy-paste examples:

```bash
python generate_video.py "城市" "chéng shì" "city; town; urban area"
```

```bash
python generate_video.py "学生" "xué shēng" "student"
```

```bash
python generate_video.py "爱" "ài" "love"
```

```bash
python generate_video.py "猫狗" "māo gǒu" "cat; dog"
```

```bash
python generate_video.py "中国" "zhōng guó" "China" --voice zh-CN-YunxiNeural
```

### Template for batch generation:

```bash
python generate_video.py "你好" "nǐ hǎo" "hello"
python generate_video.py "谢谢" "xiè xie" "thank you"
python generate_video.py "老师" "lǎo shī" "teacher"
python generate_video.py "电话" "diàn huà" "telephone"
python generate_video.py "朋友" "péng you" "friend"
```

### Output

- Video is saved to the working directory as `<characters>_stroke.mp4`
- Use `-o filename.mp4` to specify a custom output path
- Video format: 576x1024 MP4 (H.264 + AAC audio)

---

## Requirements

- **Python 3.10+**
- **ffmpeg** (must be in PATH)
- Python packages:
  ```bash
  pip install playwright edge-tts
  playwright install chromium
  ```

## Optional Flags

| Flag | Description | Default |
|------|-------------|---------|
| `-o`, `--output` | Output file path | `<characters>_stroke.mp4` |
| `--voice` | TTS voice name (see below) | `zh-CN-XiaoxiaoNeural` |
| `--no-audio` | Generate video without audio | Audio enabled |

### Available TTS Voices

| Voice ID | Description |
|----------|-------------|
| `zh-CN-XiaoxiaoNeural` | Female, natural (default) |
| `zh-CN-XiaoyiNeural` | Female, warm |
| `zh-CN-YunxiNeural` | Male, conversational |
| `zh-CN-YunjianNeural` | Male, formal |

## How It Works

1. **Stroke data** is loaded from the [Hanzi Writer](https://hanziwriter.org/) open-source library, which provides SVG paths for each stroke of thousands of Chinese characters in correct writing order.

2. **Animation** is rendered in a headless Chromium browser via Playwright. Characters appear as light gray ghost outlines, then each stroke is drawn in black following standard Chinese calligraphy stroke order.

3. **Audio** is generated using Microsoft Edge TTS (neural voices) for natural-sounding pronunciation.

4. **Video** is compiled with ffmpeg into H.264 MP4 format at 576x1024 resolution.

## Pinyin Tone Marks Reference

Copy these characters when typing pinyin:

| Tone | a | e | i | o | u | u (v) |
|------|---|---|---|---|---|--------|
| 1st (flat) | ā | ē | ī | ō | ū | ǖ |
| 2nd (rising) | á | é | í | ó | ú | ǘ |
| 3rd (dip) | ǎ | ě | ǐ | ǒ | ǔ | ǚ |
| 4th (falling) | à | è | ì | ò | ù | ǜ |

Tip: You can copy pinyin with tone marks from online dictionaries like [MDBG](https://www.mdbg.net/chinese/dictionary).

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `ffmpeg not found` | Install ffmpeg and add it to your system PATH |
| `playwright not installed` | Run `pip install playwright` then `playwright install chromium` |
| Character not rendering | The dataset covers 9000+ characters. Very rare characters may not be available |
| No audio generated | Requires internet connection for Edge TTS. Use `--no-audio` as fallback |
| Blank video at start | Requires internet to load Hanzi Writer library from CDN |
