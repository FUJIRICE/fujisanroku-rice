"""Extract the previously published wind-blown rice scene into a seamless loop."""
import json
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "static/video/hero-2026.mp4"
OUTPUT = ROOT / "static/video/hero-rice-wind-20261101.mp4"


def run(*args):
    subprocess.run(args, check=True)


def main():
    if OUTPUT.exists():
        raise SystemExit("Output exists; choose a new version before rebuilding.")
    with tempfile.TemporaryDirectory(prefix="fuji-wind-hero-") as tmp:
        clip = Path(tmp) / "wind.mp4"
        # Exclude the preceding combine scene and the original fade back to spring.
        run("ffmpeg", "-hide_banner", "-loglevel", "error", "-ss", "17",
            "-t", "2.2", "-i", str(SOURCE), "-vf",
            "eq=gamma=1.07:gamma_weight=0.7,setpts=2*PTS,minterpolate=fps=30:mi_mode=blend",
            "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "20",
            "-pix_fmt", "yuv420p", str(clip))
        info = json.loads(subprocess.check_output([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "json", str(clip),
        ]))
        fade = 0.5
        offset = float(info["format"]["duration"]) - 2 * fade
        graph = (
            f"[0:v]split[a][b];[a]trim=start={fade},setpts=PTS-STARTPTS[body];"
            f"[b]trim=end={fade},setpts=PTS-STARTPTS[head];"
            f"[body][head]xfade=transition=fade:duration={fade}:offset={offset},"
            "format=yuv420p[out]"
        )
        run("ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(clip),
            "-filter_complex", graph, "-map", "[out]", "-an", "-c:v", "libx264",
            "-preset", "slow", "-crf", "23", "-movflags", "+faststart", str(OUTPUT))
    print(json.dumps({"video": str(OUTPUT), "bytes": OUTPUT.stat().st_size}))


if __name__ == "__main__":
    main()
