#!/usr/bin/env python3
"""Generate animated GIF for Step 1: Installation."""
from PIL import Image, ImageDraw, ImageFont
import math

def main():
    W, H = 900, 500
    FPS = 12
    TOTAL = 180  # 15 seconds

    try:
        f11 = ImageFont.truetype("cour.ttf", 11)
        f9 = ImageFont.truetype("cour.ttf", 9)
        f14 = ImageFont.truetype("courbd.ttf", 14)
    except OSError:
        f11 = f9 = f14 = ImageFont.load_default()

    # Each line: (text, color, start_frame, duration, speed_type)
    # text can be a function(frame) -> str to support typing animation
    all_lines = [
        ("", '#666', 0, 5, 'wait'),
        ("git clone https://github.com/Lelolima/ShadowForge-Agent.git", '#76B900', 5, 25, 'type'),
        ("Cloning into 'ShadowForge-Agent'...", '#999', 15, 30, 'show'),
        ("done.\n", '#76B900', 35, 5, 'show'),
        ("cd ShadowForge-Agent", '#76B900', 40, 15, 'type'),
        ("python -m venv .venv", '#76B900', 60, 15, 'type'),
        ("Creating virtual environment...", '#999', 70, 20, 'show'),
        ("done.\n", '#76B900', 85, 5, 'show'),
        ("source .venv/bin/activate", '#76B900', 90, 20, 'type'),
        ("(.venv) root@shadowforge:~/ShadowForge-Agent$", '#76B900', 100, 5, 'show'),
        ("pip install -r requirements.txt", '#76B900', 105, 40, 'type'),
        ("Collecting requests>=2.31.0 ........................ done", '#999', 115, 25, 'show'),
        ("Collecting numpy>=1.24.0 ........................... done", '#999', 120, 25, 'show'),
        ("Collecting pydantic-settings>=2.0 ................ done", '#999', 125, 25, 'show'),
        ("Collecting torch>=2.0 ............................ done", '#999', 130, 20, 'show'),
        ("Successfully installed 43 packages", '#76B900', 140, 10, 'show'),
        ("cp .env.example .env", '#76B900', 155, 15, 'type'),
        ("nano .env", '#76B900', 170, 10, 'type'),
        ("", '#666', 180, TOTAL-180, 'wait'),
    ]

    frames = []

    for frame in range(TOTAL):
        img = Image.new('RGB', (W, H), '#050505')
        draw = ImageDraw.Draw(img)

        # Title bar
        draw.rectangle([0, 0, W, 30], fill='#0a0a0a', outline='#222', width=1)
        draw.text((10, 6), "STEP 1/6: INSTALLATION", fill='#76B900', font=f14)
        draw.text((W-280, 6), "python -m venv .venv && source .venv/bin/activate", fill='#444', font=f9)

        # Build current active lines based on frame
        active_lines = []
        prompt = "root@shadowforge:~$ "
        for text, color, start, dur, mode in all_lines:
            if frame >= start:
                elapsed = frame - start
                if mode == 'wait':
                    active_lines.append((text, color))
                elif mode == 'type':
                    # Typing animation: show chars progressively
                    chars_to_show = min(len(text), int(elapsed * 3))
                    shown = text[:chars_to_show]
                    if shown:
                        active_lines.append((shown, color))
                elif mode == 'show':
                    if elapsed < dur:
                        active_lines.append((text, color))
                    else:
                        # Keep old lines visible briefly
                        if elapsed < dur + 100:
                            active_lines.append((text, color))

        # Keep only last 10 lines visible
        visible_lines = active_lines[-10:]

        # Render visible lines
        y = 40
        for text, color in visible_lines:
            draw.text((10, y), f"$ ", fill='#76B900', font=f11)
            # Handle multi-line (like done.\n)
            for subline in text.split('\n'):
                if subline.strip():
                    draw.text((20, y), subline, fill=color, font=f11)
                y += 18

        # Blinking cursor
        if frame % 12 < 6:
            draw.rectangle([20, y-2, 22, y+12], fill='#76B900')

        # Progress bar
        progress = min(frame / 180, 1.0)
        bar_w = int((W - 40) * progress)
        draw.rectangle([20, H-24, W-20, H-8], outline='#333', width=1, fill='#111')
        if bar_w > 0:
            draw.rectangle([20, H-24, 20 + bar_w, H-8], fill='#1a3000', outline='#76B900', width=1)
        draw.text((W//2 - 40, H-22), f"Installing... {int(progress * 100)}%", fill='#76B900', font=f9)

        frames.append(img)

    frames[0].save(
        'install-shadowforge.gif',
        save_all=True,
        append_images=frames[1:],
        duration=int(1000/FPS),
        loop=0,
        optimize=True
    )
    print("GIF saved: install-shadowforge.gif")

if __name__ == "__main__":
    main()
