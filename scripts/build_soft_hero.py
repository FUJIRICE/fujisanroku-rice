"""Build the calmer hero from the preserved original; requires ffmpeg/ffprobe.

Usage: python3 scripts/build_soft_hero.py
The original remains unchanged. Output paths must not already exist.
"""
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "static/video/hero-2026.mp4"
OUTPUT = ROOT / "static/video/hero-2026-soft-20261101.mp4"
POSTER = ROOT / "static/images/season/hero-poster-soft-20261101.jpg"


def run(*args):
    subprocess.run(args, check=True)


def duration(path):
    result = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "json", str(path),
    ])
    return float(json.loads(result)["format"]["duration"])


def main():
    if OUTPUT.exists() or POSTER.exists():
        raise SystemExit("Output already exists; choose a new version before rebuilding.")
    with tempfile.TemporaryDirectory(prefix="fuji-soft-hero-") as tmp:
        smooth = Path(tmp) / "smooth.mp4"
        # Normalize short exposure changes before blending, retain actual farm footage,
        # and slow seasonal changes to half speed; blend intermediate frames at 30 fps.
        filters = (
            "deflicker=size=21:mode=am,"
            "tmix=frames=9:weights='1 2 3 4 5 4 3 2 1',"
            "eq=gamma=1.12:gamma_weight=0.7:saturation=1.02,"
            "setpts=2*PTS,minterpolate=fps=30:mi_mode=blend"
        )
        run("ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(SOURCE),
            "-vf", filters, "-an", "-c:v", "libx264", "-preset", "fast",
            "-crf", "22", "-pix_fmt", "yuv420p", str(smooth))
        fade = 1.5
        # End with the opening 1.5 seconds, crossfaded over the ending scene.
        # Start at 1.5 seconds so the native loop continues to the very next frame.
        offset = duration(smooth) - 2 * fade
        graph = (
            f"[0:v]split[a][b];[a]trim=start={fade},setpts=PTS-STARTPTS[body];"
            f"[b]trim=end={fade},setpts=PTS-STARTPTS[head];"
            f"[body][head]xfade=transition=fade:duration={fade}:offset={offset},"
            "format=yuv420p[out]"
        )
        run("ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(smooth),
            "-filter_complex", graph, "-map", "[out]", "-an", "-c:v", "libx264",
            "-preset", "slow", "-crf", "24", "-movflags", "+faststart", str(OUTPUT))
        # Use the first video frame as the poster to avoid a flash on autoplay start.
        run("ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(OUTPUT),
            "-frames:v", "1", "-q:v", "2", str(POSTER))
    print(json.dumps({"video": str(OUTPUT), "seconds": duration(OUTPUT),
                      "bytes": OUTPUT.stat().st_size, "poster": str(POSTER)}))


if __name__ == "__main__":
    main()
