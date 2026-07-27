#!/usr/bin/env python3
"""Generate optimized animated GIF of the ShadowForge dashboard."""
from PIL import Image, ImageDraw, ImageFont
import math

def main():
    W, H = 1280, 580
    FPS = 10
    DURATION = 5  # seconds
    TOTAL = FPS * DURATION

    try:
        f8  = ImageFont.truetype("cour.ttf", 8)
        f9  = ImageFont.truetype("cour.ttf", 9)
        f10 = ImageFont.truetype("cour.ttf", 10)
        f11 = ImageFont.truetype("courbd.ttf", 11)
        f14 = ImageFont.truetype("courbd.ttf", 14)
        f22 = ImageFont.truetype("arialbd.ttf", 22)
    except OSError:
        f8 = f9 = f10 = f11 = f14 = f22 = ImageFont.load_default()

    frames = []

    for frame in range(TOTAL):
        img = Image.new('RGB', (W, H), '#050505')
        draw = ImageDraw.Draw(img)

        # ── Header ──
        draw.rectangle([0, 0, W, 55], fill='#0a0a0a')
        draw.line([(0, 55), (W, 55)], fill='#222', width=1)
        draw.rounded_rectangle([20, 8, 60, 42], radius=4, outline='#76B900', width=2)
        draw.text((40, 25), "SF", fill='#76B900', font=f14, anchor="mm")
        draw.text((75, 25), "SH4D0WF0RG3", fill='#fff', font=f22)
        draw.text((285, 22), "v1.0.0", fill='#76B900', font=f11)
        draw.text((75, 42), "AUTONOMOUS ETHICAL HACKING AI // NVIDIA NIM CONNECTED", fill='#666', font=f9)
        for i, (lab, val, col) in enumerate([("GPU LOAD","87%",'#76B900'),("VRAM","22.4 GB",'#76B900'),
                                              ("INFERENCE","12ms",'#60a5fa'),("MODE","STEALTH",'#fbbf24')]
         ):
            x = 960 + i*90
            draw.text((x, 12), lab, fill='#666', font=f9)
            draw.text((x, 32), val, fill=col, font=f11)

        # ── LEFT: OODA + Modules ──
        px, py = 15, 65
        pw = 240
        draw.rectangle([px, py, px+pw, py+420], fill='#0a0a0a', outline='#222', width=1)
        draw.rectangle([px, py, px+pw, py+24], fill='#111')
        draw.text((px+10, py+8), "OODA LOOP ENGINE", fill='#76B900', font=f11)
        steps = ['OBSERVE', 'ORIENT', 'DECIDE', 'ACT']
        active_idx = (frame // 12) % 4
        for i, s in enumerate(steps):
            sx = px + 8 + i*(56)
            color = '#76B900' if i == active_idx else '#333'
            bg = '#1a3000' if i == active_idx else '#111'
            draw.rectangle([sx, py+32, sx+52, py+58], fill=bg, outline=color, width=1)
            draw.text((sx + 26, py+46), s, fill=color if i == active_idx else '#666', font=f9, anchor="mm")
        draw.text((px+10, py+68), "CYCLE TIME: 145ms", fill='#fff', font=f9)
        draw.text((px+10, py+92), "ACTIVE MODULES", fill='#76B900', font=f11)
        modules = [
            ("Screen Capture", True), ("Nemotron Vision", True), ("YOLOv8 Detector", True),
            ("Mouse Control", False), ("Keyboard Inject", False), ("Stealth Shell", True),
            ("Network Sniffer", True), ("Report Generator", False)
        ]
        for i, (name, active) in enumerate(modules):
            my = py + 112 + i*22
            draw.rectangle([px+5, my, px+pw-5, my+20], fill='#111')
            draw.text((px+10, my+5), name, fill='#ccc' if active else '#555', font=f8)
            status = "ACTIVE" if active else "IDLE"
            color = '#76B900' if active else '#fbbf24'
            draw.text((px+pw-50, my+5), status, fill=color, font=f8)
            dot_c = '#76B900' if active else '#fbbf24'
            if active:
                pulse = 3 + int(2 * abs(math.sin(frame*0.2 + i)))
                cx, cy = px+pw-15, my+10
                draw.ellipse([cx-pulse, cy-pulse, cx+pulse, cy+pulse], fill=dot_c)
            else:
                draw.ellipse([px+pw-18, my+7, px+pw-12, my+13], fill=dot_c)

        # ── CENTER: Terminal ──
        tx, ty = 280, 65
        tw = 540
        draw.rectangle([tx, ty, tx+tw, ty+255], fill='#0a0a0a', outline='#222', width=1)
        draw.rectangle([tx, ty, tx+tw, ty+28], fill='#111')
        draw.ellipse([tx+16, ty+10, tx+24, ty+18], fill='#ef4444')
        draw.ellipse([tx+31, ty+10, tx+39, ty+18], fill='#fbbf24')
        draw.ellipse([tx+46, ty+10, tx+54, ty+18], fill='#22c55e')
        draw.text((tx+65, ty+18), "root@shadowforge:~/campaign_alpha — python main.py --mode stealth", fill='#666', font=f9)
        scan_y = ty + 28 + (frame * 4) % (255-30)
        draw.rectangle([tx, scan_y-1, tx+tw, scan_y+1], fill='#76B900')
        lines = [
            ("# Initializing SH4D0WF0RG3 Core v1.0.0...", '#666'),
            ("[✓] NVIDIA NIM Endpoint Connected (Llama-3.3-70B)", '#76B900'),
            ("[✓] Riva ASR/TTS Stream Established (Latency: 12ms)", '#76B900'),
            ("[✓] Ethical Guardrails: ENGAGED (Strict Mode)", '#76B900'),
            ("> Target Authorization Verified: 192.168.1.0/24 (LAB_ENV)", '#fff'),
            ("> Starting OODA Loop in STEALTH mode...", '#60a5fa'),
            ("[RECON] Passive OSINT gathering initiated...", '#999'),
            ("[SCAN] Discovered open port 8080 (HTTP-Proxy)", '#fbbf24'),
            ("[ENUM] Service fingerprint: Apache/2.4.52", '#999'),
            ("[AI] Analyzing attack surface... 3 vectors found", '#76B900'),
            ("[SAFE] Skipping unauthorized exploit attempt", '#60a5fa'),
        ]
        start_y = ty+40
        for i, (line, col) in enumerate(lines):
            draw.text((tx+15, start_y+i*16), line, fill=col, font=f9)
        if frame % 10 < 5:
            draw.rectangle([tx+15, start_y+len(lines)*16+3, tx+17, start_y+len(lines)*16+13], fill='#76B900')
        draw.text((tx+15, start_y+len(lines)*16), "> ", fill='#76B900', font=f9)

        # Vision feed
        vx, vy = 280, 330
        vw = 540
        draw.rectangle([vx, vy, vx+vw, vy+155], fill='#050505', outline='#222', width=1)
        draw.rectangle([vx, vy, vx+vw, vy+24], fill='#111')
        draw.text((vx+10, vy+8), "LIVE_FEED // YOLOv8 + OCR ACTIVE", fill='#76B900', font=f9)
        draw.text((vx+vw-150, vy+8), "NEMOTRON MULTIMODAL INFERENCE", fill='#76B900', font=f8)
        vscan = vy + (frame * 4) % 155
        draw.rectangle([vx, vscan-1, vx+vw, vscan+1], fill='#76B900')
        draw.rectangle([vx+50, vy+40, vx+200, vy+110], outline='#76B900', width=2)
        draw.text((vx+52, vy+38), "TERMINAL [99%]", fill='#76B900', font=f8)
        draw.rectangle([vx+250, vy+60, vx+400, vy+120], outline='#60a5fa', width=2)
        draw.text((vx+252, vy+58), "BROWSER_UI [94%]", fill='#60a5fa', font=f8)
        draw.text((vx+vw//2, vy+77), "PROCESSING VISUAL STREAM...", fill='#76B900', font=f10, anchor="mm")

        # ── RIGHT: Kill Chain ──
        rx, ry = 840, 65
        rw = 420
        draw.rectangle([rx, ry, rx+rw, ry+250], fill='#0a0a0a', outline='#222', width=1)
        draw.rectangle([rx, ry, rx+rw, ry+24], fill='#111')
        draw.text((rx+10, ry+8), "KILL CHAIN STATE", fill='#76B900', font=f11)
        kc_steps = [('RECON','Nmap,Shodan'), ('SCAN','Port Scan'), ('ENUM','Service Enum'),
                    ('EXPLOIT','PoC Gen'), ('POST','Privesc'), ('REPORT','PDF/HTML')]
        kc_idx = (frame // 20) % 6
        for i, (lab, desc) in enumerate(kc_steps):
            ky = ry + 38 + i*34
            if i < kc_idx:
                border, bg, txt = '#76B900', '#1a3000', '#76B900'
            elif i == kc_idx:
                border, bg, txt = '#76B900', '#0a1a00', '#fff'
            else:
                border, bg, txt = '#333', '#111', '#666'
            draw.rectangle([rx+10, ky, rx+rw-10, ky+30], fill=bg, outline=border, width=1)
            draw.text((rx+20, ky+7), lab, fill=txt, font=f10)
            draw.text((rx+150, ky+7), desc, fill='#666666' if i != kc_idx else '#76B900', font=f9)
            if i == kc_idx:
                draw.ellipse([rx+rw-28, ky+12, rx+rw-20, ky+20], fill='#76B900')

        # Audit Trail
        ax, ay = 840, 325
        aw = 420
        draw.rectangle([ax, ay, ax+aw, ay+160], fill='#0a0a0a', outline='#222', width=1)
        draw.rectangle([ax, ay, ax+aw, ay+24], fill='#111')
        draw.text((ax+10, ay+8), "AUDIT TRAIL", fill='#76B900', font=f11)
        draw.text((ax+aw-70, ay+8), "ENCRYPTED", fill='#60a5fa', font=f9)
        logs = [
            ("[VISION] Detected input field: 'admin_login'", '#999'),
            ("[OCR] Extracted hash: 5d41402abc4b2a76...", '#a855f7'),
            ("[NET] Port 443 open (HTTPS/TLS1.3)", '#999'),
            ("[AI] Potential SQLi vector identified", '#76B900'),
            ("[GUARD] Blocked command: rm -rf", '#60a5fa'),
            ("[RIVA] Voice: 'Enumerate services'", '#a855f7'),
            ("[NIM] Inference completed (45ms)", '#76B900'),
            ("[SAFE] PII detected and redacted", '#60a5fa'),
        ]
        for i, (log, col) in enumerate(logs):
            draw.text((ax+10, ay+38+i*14), log, fill=col, font=f8)

        # Voice
        draw.rectangle([ax, ay+160+8, ax+aw, ay+160+132], fill='#0a0a0a', outline='#222', width=1)
        draw.rectangle([ax, ay+160+8, ax+aw, ay+160+32], fill='#111')
        draw.text((ax+10, ay+160+16), "VOICE INTERFACE", fill='#76B900', font=f11)
        draw.text((ax+aw-100, ay+160+16), "NVIDIA RIVA ASR/TTS", fill='#76B900', font=f8)
        by = ay + 160 + 25
        for bi in range(35):
            bar_h = 5 + abs(int(40 * math.sin(frame*0.3 + bi*0.4)))
            alpha = int(100 + 155 * abs(math.sin(frame*0.15 + bi*0.2)))
            bx = ax + 20 + bi*10
            r = int(118 * alpha / 255)
            g = int(185 * alpha / 255)
            draw.rectangle([bx, by, bx+5, by+min(bar_h, 45)], fill=(r, g, 0))
        draw.text((ax+10, by+55), "● LISTENING", fill='#76B900', font=f9)
        draw.text((ax+10, by+70), "> \"Initialize stealth recon on target...\"", fill='#666', font=f8)

        # Ethical Guardrails
        draw.rectangle([15, 490, 835, 515], fill='#111', outline='#222', width=1)
        draw.text((30, 495), "🔒 ETHICAL GUARDRAILS", fill='#60a5fa', font=f11)
        draw.text((250, 498), "| Unauthorized actions blocked | Destructive commands filtered | PII redaction active", fill='#60a5fa', font=f9)

        # Matrix rain (minimal)
        for mx in range(0, W, 30):
            for j in range(3):
                my = int((frame*8 + mx*j) % H)
                if my > 55 and my < 490:
                    alpha = int(30 + 40 * abs(math.sin(frame*0.1 + mx)))
                    draw.point((mx, my), fill=(0, alpha, 0))

        frames.append(img)

    # Save optimized GIF
    frames[0].save(
        'shadowforge-dashboard.gif',
        save_all=True,
        append_images=frames[1:],
        duration=1000//FPS,
        loop=0,
        optimize=True,
    )
    print("GIF saved: shadowforge-dashboard.gif")

if __name__ == "__main__":
    main()
