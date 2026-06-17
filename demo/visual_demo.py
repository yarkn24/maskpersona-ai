#!/usr/bin/env python3
"""
MaskPersona AI terminal demo
────────────────────────────
A face made of static (░) resolves into a persona as ingestion runs.
Left panel: live log stream. Right panel: morphing ASCII face.

Usage:
    python demo/visual_demo.py "John Doe"
    python demo/visual_demo.py "John Doe" --image path/to/photo.jpg
    python demo/visual_demo.py "Some Public Figure" --image photo.jpg

Pass any name and a local photo at runtime; nothing here is tied to a specific person.

Generate a face constant from any photo first:
    python demo/gen_face.py path/to/photo.jpg

To record the terminal output, use any screen-recording tool available on your platform.
"""
from __future__ import annotations

import argparse
import random
import sys
import time

try:
    from rich.console import Console
    from rich.layout import Layout
    from rich.live import Live
    from rich.panel import Panel
    from rich.text import Text
except ModuleNotFoundError:
    sys.exit("This demo needs 'rich'. Install demo extras: pip install \"MaskPersona AI[demo]\"  (or: pip install rich)")

# ── CLI ────────────────────────────────────────────────────────────────────
_parser = argparse.ArgumentParser(add_help=False)
_parser.add_argument("name", nargs="*", default=["John Doe"])
_parser.add_argument("--image", default=None, help="photo file to use as target face")
_parser.add_argument("--invert", action="store_true", help="invert brightness (light-bg photos)")
_parser.add_argument("--width", type=int, default=49)
_parser.add_argument("--height", type=int, default=28)
_args, _ = _parser.parse_known_args()

TARGET_NAME: str = " ".join(_args.name) if _args.name else "John Doe"
IMAGE_SOURCE: str | None = _args.image
_FACE_W: int = _args.width
_FACE_H: int = _args.height

# ── Face helpers ───────────────────────────────────────────────────────────

def _pad(lines: list[str], w: int = _FACE_W, h: int = _FACE_H) -> list[str]:
    out = [line.ljust(w)[:w] for line in lines]
    while len(out) < h:
        out.append(" " * w)
    return out[:h]


def _blank() -> list[str]:
    return _pad(["░" * _FACE_W] * _FACE_H)


def _face_from_image_ascii_magic(source: str) -> list[str] | None:
    """Use ascii_magic library for best quality conversion."""
    try:
        from ascii_magic import AsciiArt
        art = AsciiArt.from_image(source)
        raw = art.to_ascii(columns=_FACE_W, monochrome=True)
        lines = raw.splitlines()
        return _pad(lines)
    except Exception as exc:
        print(f"[warn] ascii_magic failed: {exc}", file=sys.stderr)
        return None


def _face_from_image_pil(source: str) -> list[str] | None:
    """PIL fallback: grayscale + resize + char ramp."""
    try:
        from PIL import Image

        img = Image.open(source)
        img = img.convert("L")
        img = img.resize((_FACE_W, _FACE_H * 2), Image.LANCZOS)
        img = img.resize((_FACE_W, _FACE_H), Image.LANCZOS)

        CHARS = " .'`^\":;-~+=<>|()IltfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"
        rows: list[str] = []
        for y in range(_FACE_H):
            row = ""
            for x in range(_FACE_W):
                brightness = img.getpixel((x, y))
                if _args.invert:
                    idx = int(brightness / 255 * (len(CHARS) - 1))
                else:
                    idx = int((255 - brightness) / 255 * (len(CHARS) - 1))
                row += CHARS[max(0, min(idx, len(CHARS) - 1))]
            rows.append(row)
        return rows
    except Exception as exc:
        print(f"[warn] PIL conversion failed: {exc}", file=sys.stderr)
        return None


def _load_target_face() -> list[str]:
    if not IMAGE_SOURCE:
        return _blank()  # no image: morph stays as noise (placeholder)
    face = _face_from_image_ascii_magic(IMAGE_SOURCE)
    if face:
        return face
    face = _face_from_image_pil(IMAGE_SOURCE)
    if face:
        return face
    print("[warn] could not load image, showing noise only", file=sys.stderr)
    return _blank()


TARGET_FACE: list[str] = _load_target_face()
BLANK: list[str] = _blank()

# ── Morph helpers ──────────────────────────────────────────────────────────

def _all_positions() -> list[tuple[int, int]]:
    return [(r, c) for r in range(_FACE_H) for c in range(_FACE_W)]


def build_morph_frames(
    source: list[str],
    target: list[str],
    n_frames: int,
) -> list[list[str]]:
    """Random-reveal morph with quadratic easing (slow start, fast finish)."""
    positions = _all_positions()
    random.shuffle(positions)
    total = len(positions)

    def revealed_count(frame: int) -> int:
        t = frame / n_frames
        return int((t * t) * total)

    grid = [list(row) for row in source]
    frames: list[list[str]] = []
    prev_n = 0

    for f in range(n_frames + 1):
        n = revealed_count(f)
        for idx in range(prev_n, n):
            r, c = positions[idx]
            grid[r][c] = target[r][c]
        prev_n = n
        frames.append(["".join(row) for row in grid])

    return frames


# ── Fake log messages ──────────────────────────────────────────────────────

def _make_log(name: str) -> list[str]:
    slug = name.lower().replace(" ", "_")
    return [
        f"[bold cyan]>[/] MaskPersona AI ingest --persona {name}",
        "[dim]  loading constitution... OK[/]",
        "[dim]  public-figure gate: confirmed[/]",
        "[green]o[/] discovering public content sources",
        "[dim]  found 847 articles, 34 talks, 12 interviews[/]",
        "[dim]  estimated 2.1 GB raw text[/]",
        "[green]o[/] fetching articles (1/847)",
        "[dim]  chunk 0001: indexing public article...[/]",
        "[dim]  chunk 0002: indexing interview transcript...[/]",
        "[dim]  chunk 0045: indexing talk transcript...[/]",
        "[green]o[/] transcribing talks (1/34)",
        "[dim]  talk 001: whisper large-v3 (local)[/]",
        "[dim]  voice fingerprint: matched solo segments[/]",
        "[dim]  extracting key passages...[/]",
        "[green]o[/] embedding chunks (381/847)",
        "[dim]  batch 12/54: OK (0.4s)[/]",
        "[dim]  batch 13/54: OK (0.3s)[/]",
        "[green]o[/] embedding chunks (612/847)",
        "[dim]  storing in brain/mempalace...[/]",
        "[dim]  nodes: 1,247  edges: 3,891[/]",
        "[green]o[/] building knowledge graph",
        "[dim]  linking citations...[/]",
        "[dim]  inferring topic clusters...[/]",
        "[dim]  detected topic clusters from public content[/]",
        "[green]o[/] embedding chunks (847/847)",
        "[dim]  final sync...[/]",
        "[dim]  checksum: a3f9e1c7  OK[/]",
        "[green]o[/] rendering persona agent",
        "[dim]  template: persona-agent.md.j2[/]",
        f"[dim]  writing .claude/agents/{slug}.md[/]",
        "[bold green]v[/] persona ready",
        f"[bold yellow]  {name} is now available as /{slug}[/]",
    ]


def _log_scroll(lines: list[str], tick: int, visible: int = 12) -> list[str]:
    end = min(tick + 1, len(lines))
    start = max(0, end - visible)
    return lines[start:end]


# ── Rich panels ────────────────────────────────────────────────────────────

def _face_panel(frame_lines: list[str], pct: int, done: bool) -> Panel:
    label = (
        f"[bold green]READY  {TARGET_NAME}[/]"
        if done
        else f"[bold yellow]persona forming... {pct}%[/]"
    )
    face_text = Text("\n".join(frame_lines), style="bright_green" if done else "green")
    return Panel(face_text, title=label,
                 border_style="bright_green" if done else "yellow", padding=(0, 1))


def _log_panel(visible_lines: list[str]) -> Panel:
    return Panel(Text.from_markup("\n".join(visible_lines)),
                 title="[bold]ingestion log[/]", border_style="cyan", padding=(0, 1))


# ── Animation ──────────────────────────────────────────────────────────────

TOTAL_SECONDS = 20
FPS = 12
N_MORPH_FRAMES = TOTAL_SECONDS * FPS


def run() -> None:
    console = Console()
    log_lines = _make_log(TARGET_NAME)

    frames = build_morph_frames(BLANK, TARGET_FACE, n_frames=N_MORPH_FRAMES)
    total_frames = len(frames)
    log_tick_per_frame = len(log_lines) / total_frames

    layout = Layout()
    layout.split_row(
        Layout(name="log", ratio=2),
        Layout(name="face", ratio=3),
    )

    with Live(layout, refresh_per_second=FPS, screen=False, console=console):
        for f_idx, frame in enumerate(frames):
            pct = int(f_idx / total_frames * 100)
            done = f_idx == total_frames - 1
            log_tick = int(f_idx * log_tick_per_frame)
            layout["face"].update(_face_panel(frame, pct, done))
            layout["log"].update(_log_panel(_log_scroll(log_lines, log_tick)))
            time.sleep(1 / FPS)
        time.sleep(2)

    slug = TARGET_NAME.lower().replace(" ", "_")
    console.print(
        f"\n[bold green]v[/] [white]{TARGET_NAME}[/] persona is ready. "
        f"[dim]Start a conversation with /{slug}[/]\n"
    )


if __name__ == "__main__":
    run()
