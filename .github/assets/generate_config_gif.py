#!/usr/bin/env python3
"""Generate animated GIF for Step 2: Configuration."""
from PIL import Image, ImageDraw, ImageFont


def main():
    W, H = 900, 500
    FPS = 12
    TOTAL = 180

    try:
        f11 = ImageFont.truetype("cour.ttf", 11)
        f9 = ImageFont.truetype("cour.ttf", 9)
        f14 = ImageFont.truetype("courbd.ttf", 14)
    except OSError:
        f11 = f9 = f14 = ImageFont.load_default()

    # (text, color, start_frame, end_frame, column_index)
    all_events = [
        # INIT CONFIG PHASE
        ("cat .env", '#76B900', 0, 15, 0),
        ("# NVIDIA API Settings", '#666', 5, 180, 0),
        ("NVIDIA_API_KEY=", '#fff', 15, 180, 0),
        ("", '', 25, 180, 0),

        # TYPING API KEY
        ("NVIDIA_API_KEY=nvapi-", '#fff', 30, 50, 0),
        ("NVIDIA_API_KEY=nvapi-qw8", '#fff', 35, 50, 0),
        ("NVIDIA_API_KEY=nvapi-qw8x9", '#fff', 38, 50, 0),
        ("NVIDIA_API_KEY=nvapi-qw8x9pL2", '#fff', 42, 50, 0),
        ("NVIDIA_API_KEY=nvapi-qw8x9pL2mN4", '#fff', 45, 50, 0),
        ("NVIDIA_API_KEY=nvapi-********************************", '#fbbf24', 50, 180, 0),

        # CONFIG MODEL
        ("NVIDIA_MODEL=meta/llama-3.3-70b-instruct", '#fff', 55, 180, 0),
        ("", '', 65, 180, 0),
        ("# Vision Settings", '#666', 67, 180, 0),
        ("VISION_ENGINE=nemotron", '#999', 70, 180, 0),

        # VALIDATE RUN
        ("", '', 75, 80, 0),
        ("python scripts/validate_env.py", '#76B900', 80, 100, 0),
        ("[✓] NVIDIA API Key validated", '#76B900', 90, 180, 0),
        ("[✓] Model meta/llama-3.3-70b-instruct accessible", '#76B900', 95, 180, 0),
        ("[✓] GPU detected: RTX 4090 (24GB)", '#76B900', 100, 180, 0),
        ("[✓] All checks passed", '#76B900', 108, 180, 0),

        # HEALTH CHECK
        ("", '', 115, 120, 0),
        ("python scripts/health_check.py", '#76B900', 120, 180, 0),
        ("[✓] Core engine: OK", '#76B900', 130, 180, 0),
        ("[✓] NVIDIA NIM: Connected (12ms)", '#76B900', 133, 180, 0),
        ("[✓] Riva ASR/TTS: Ready", '#76B900', 136, 180, 0),
        ("[✓] Vision pipeline: Active", '#76B900', 139, 180, 0),
        ("", '', 148, 180, 0),
        ("✓ Configuration complete! Ready to hack.", '#76B900', 150, 155, 0),
        ("", '', 158, 180, 0),
        ("python main.py --mode stealth --target 192.168.1.0/24 --simulate", '#76B900', 160, 180, 0),

        # RIGHT COL: .env content preview
        ("# .env configuration", '#fbbf24', 5, 180, 1),
        ("", '', 10, 180, 1),
        ("NVIDIA_API_KEY=", '#fff', 20, 180, 1),
        ("********************************", '#fbbf24', 50, 180, 1),
        ("", '', 55, 180, 1),
        ("NVIDIA_MODEL=", '#fff', 57, 180, 1),
        ("meta/llama-3.3-70b-instruct", '#76B900', 60, 180, 1),
        ("", '', 67, 180, 1),
        ("VISION_ENGINE=nemotron", '#999', 70, 180, 1),
        ("STEALTH_MODE=true", '#999', 75, 180, 1),
        ("ETHICAL_CHECKS=strict", '#60a5fa', 80, 180, 1),
    ]

    frames = []

    for frame in range(TOTAL):
        img = Image.new('RGB', (W, H), '#050505')
        draw = ImageDraw.Draw(img)

        # Title bar
        draw.rectangle([0, 0, W, 30], fill='#0a0a0a', outline='#222', width=1)
        draw.text((10, 6), "STEP 2/6: CONFIGURATION", fill='#76B900', font=f14)
        draw.text((W-250, 6), "cp .env.example .env && nano .env", fill='#444', font=f9)

        # Terminal columns
        col_w = (W - 30) // 2

        # Left column: terminal output
        draw.rectangle([10, 40, 10 + col_w, H - 25], fill='#0a0a0a', outline='#333', width=1)
        draw.rectangle([10, 40, 10 + col_w, 60], fill='#111')
        draw.text((15, 45), "Terminal", fill='#333', font=f9)

        # Right column: .env preview
        draw.rectangle([20 + col_w, 40, W - 10, H - 25], fill='#0a0a0a', outline='#333', width=1)
        draw.rectangle([20 + col_w, 40, W - 10, 60], fill='#111')
        draw.text((25 + col_w, 45), ".env file", fill='#333', font=f9)

        # Render left column events
        y = 65
        for text, color, start, end, col_idx in all_events:
            if start <= frame < end and col_idx == 0:
                if text:
                    draw.text((15, y), f"$ {text}" if not text.startswith("[") and not text.startswith("✓") and not text.startswith("#") else text, fill=color, font=f11)
                    y += 18

        # Render right column (.env preview)
        y2 = 65
        for text, color, start, end, col_idx in all_events:
            if start <= frame < end and col_idx == 1:
                if text:
                    draw.text((25 + col_w, y2), text, fill=color, font=f9)
                    y2 += 16

        # Progress bar
        progress = min(frame / TOTAL, 1.0)
        bar_w = int((W - 40) * progress)
        draw.rectangle([20, H-20, W-20, H-8], outline='#333', width=1, fill='#111')
        if bar_w > 0:
            draw.rectangle([20, H-20, 20 + bar_w, H-8], fill='#1a3000', outline='#76B900', width=1)
        draw.text((W//2 - 50, H-19), f"Configuring... {int(progress * 100)}%", fill='#76B900', font=f9)

        frames.append(img)

    frames[0].save(
        'configure-shadowforge.gif',
        save_all=True,
        append_images=frames[1:],
        duration=int(1000/FPS),
        loop=0,
        optimize=True
    )
    print("GIF saved: configure-shadowforge.gif")


if __name__ == "__main__":
    main()
