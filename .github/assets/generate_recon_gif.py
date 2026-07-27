#!/usr/bin/env python3
"""Generate animated GIF for Step 3: Reconnaissance (RECON)."""
from PIL import Image, ImageDraw, ImageFont
import math
import random

def main():
    W, H = 1000, 550
    FPS = 10
    TOTAL = 200

    try:
        f11 = ImageFont.truetype("cour.ttf", 11)
        f9 = ImageFont.truetype("cour.ttf", 9)
        f14 = ImageFont.truetype("courbd.ttf", 14)
        f16 = ImageFont.truetype("courbd.ttf", 16)
    except OSError:
        f11 = f9 = f14 = f16 = ImageFont.load_default()

    # Network nodes for visualization
    random.seed(42)
    nodes = [(random.randint(100, 400), random.randint(120, 350)) for _ in range(15)]

    frames = []
    center = (500, 250)

    for frame in range(TOTAL):
        img = Image.new('RGB', (W, H), '#050505')
        draw = ImageDraw.Draw(img)

        # Title
        draw.rectangle([0, 0, W, 30], fill='#0a0a0a', outline='#222', width=1)
        draw.text((10, 6), "STEP 3/6: RECONNAISSANCE (RECON)", fill='#76B900', font=f14)
        draw.text((W-200, 6), "nmap -sV -sC 192.168.1.0/24", fill='#444', font=f9)

        # Progress bar at bottom
        progress = min(frame / TOTAL, 1.0)
        bar_w = int((W - 40) * progress)
        draw.rectangle([20, H-20, W-20, H-8], outline='#333', width=1, fill='#111')
        if bar_w > 0:
            draw.rectangle([20, H-20, 20 + bar_w, H-8], fill='#1a3000', outline='#76B900', width=1)
        draw.text((W//2 - 30, H-19), f"Recon... {int(progress * 100)}%", fill='#76B900', font=f9)

        # Left: Network visualization
        # Draw target network
        draw.rectangle([20, 40, 420, 340], fill='#0a0a0a', outline='#333', width=1)
        draw.rectangle([20, 40, 420, 60], fill='#111')
        draw.text((30, 46), "Network Topology Discovery", fill='#76B900', font=f11)

        # Draw connection lines from center
        discovered = min(frame // 15, len(nodes))
        for i, (nx, ny) in enumerate(nodes):
            if i < discovered:
                # Line from center
                alpha = int(100 + 155 * (i / len(nodes)))
                color = '#76B9008'[:7]  # Use fixed color
                draw.line([(center[0] - 240 + nx * 0.3, 200 + ny * 0.4), (center[0] - 100 + i * 15, 180 + i * 10)], fill='#76B900' if i < discovered else '#333', width=1)

        # Draw discovered nodes
        host = "192.168.1."
        for i in range(discovered):
            x = 40 + i * 25
            y = 100 + (i % 3) * 60
            pulse = 3 + int(abs(math.sin(frame * 0.2 + i)) * 4)
            draw.ellipse([x-4, y-4, x+4, y+4], fill='#76B900')
            draw.text((x+8, y-4), f"{host}{i+1}", fill='#999', font=f9)
            draw.text((x+8, y+6), f"Host {i+1}", fill='#444', font=f9)

        # Network scan stats
        discovered_hosts = min(frame // 10, 15)
        ports_found = discovered_hosts * random.randint(2, 5)
        draw.text((30, 320), f"Discovered: {discovered_hosts} hosts", fill='#76B900', font=f11)
        draw.text((30, 338), f"Open ports: {ports_found}", fill='#fbbf24', font=f9)
        draw.text((30, 354), f"Services: {ports_found // 2} identified", fill='#60a5fa', font=f9)

        # Middle: Terminal with NMAP output
        draw.rectangle([440, 40, 850, 340], fill='#0a0a0a', outline='#333', width=1)
        draw.rectangle([440, 40, 850, 60], fill='#111')
        draw.text((450, 46), "nmap -sV -sC 192.168.1.0/24 --stealth", fill='#fbbf24', font=f11)

        nmap_output = [
            "Starting Nmap 7.93 (https://nmap.org) at 2026-05-25 14:30",
            "Nmap scan report for 192.168.1.1 (router.local)",
            "Host is up (0.0003s latency).",
            "Not shown: 998 closed tcp ports (reset)",
            "PORT    STATE SERVICE",
            "22/tcp  open  ssh     OpenSSH 8.9p1",
            "80/tcp  open  http    Apache httpd 2.4.52",
            "443/tcp open  https   Apache httpd 2.4.52 (OpenSSL)",
            "",
            "Nmap scan report for 192.168.1.10 (web-server.local)",
            "Host is up (0.0002s latency).",
            "Not shown: 995 closed tcp ports (reset)",
            "PORT     STATE SERVICE",
            "22/tcp   open  ssh      OpenSSH 8.9p1",
            "80/tcp   open  http     nginx 1.18.0",
            "3306/tcp open  mysql    MySQL 8.0.33",
            "8080/tcp open  http-proxy Apache Tomcat",
            "",
            "Nmap scan report for 192.168.1.25 (db-server.local)",
            "Host is up (0.0001s latency).",
            "Not shown: 999 closed tcp ports (reset)",
            "PORT     STATE SERVICE",
            "3306/tcp open  mysql   MySQL 8.0.33",
            "5432/tcp open  postgresql PostgreSQL 14",
        ]

        # Show lines progressively
        lines_to_show = min(frame // 8, len(nmap_output))
        y = 68
        for i in range(lines_to_show):
            line = nmap_output[i]
            if not line:
                y += 10
                continue
            col = '#999'
            if line.startswith("PORT") or line.startswith("Nmap scan"):
                col = '#76B900'
            elif 'open' in line:
                col = '#22c55e'
            elif 'closed' in line:
                col = '#ef4444'
            draw.text((450, y), line, fill=col, font=f9)
            y += 13

        # Right: OSINT Panel
        draw.rectangle([870, 40, W-20, 340], fill='#0a0a0a', outline='#333', width=1)
        draw.rectangle([870, 40, W-20, 60], fill='#111')
        draw.text((880, 46), "OSINT Intelligence", fill='#76B900', font=f11)

        osint_lines = [
            ("WHOIS target.com", '#76B900'),
            ("Registrar: Cloudflare, Inc.", '#999'),
            ("Created: 2015-03-12", '#999'),
            ("Last updated: 2025-01-15", '#999'),
            ("", '#000'),
            ("DNS Records:", '#76B900'),
            ("  A    target.com       104.16.1.1", '#999'),
            ("  A    www.target.com   104.16.1.2", '#999'),
            ("  MX   mail.target.com 198.51.100.5", '#999'),
            ("  TXT  v=spf1 mx -all", '#60a5fa'),
            ("", '#000'),
            ("Shodan Results:", '#76B900'),
            ("  Found 3 devices", '#fbbf24'),
            ("  Port 80: Apache/2.4", '#999'),
            ("  Port 443: nginx/1.18", '#999'),
        ]

        lines_to_show = min(frame // 12, len(osint_lines))
        y = 70
        for i in range(lines_to_show):
            text, col = osint_lines[i]
            draw.text((880, y), text, fill=col, font=f9)
            y += 16

        # Middle bottom: Subdomain enumeration
        draw.rectangle([440, 360, 850, 500], fill='#0a0a0a', outline='#333', width=1)
        draw.rectangle([440, 360, 850, 380], fill='#111')
        draw.text((450, 366), "Subdomain Enumeration", fill='#76B900', font=f11)

        subdomains = [
            ("subfinder -d target.com | sort -u", '#fbbf24'),
            ("admin.target.com", '#76B900'),
            ("api.target.com", '#76B900'),
            ("dev.target.com", '#76B900'),
            ("staging.target.com", '#76B900'),
            ("beta.target.com", '#999'),
            ("mail.target.com", '#999'),
            ("", '#000'),
            ("Total subdomains found: 7", '#fbbf24'),
            ("Potential targets: admin, api", '#ef4444'),
        ]

        lines_to_show = min(frame // 15, len(subdomains))
        y = 392
        for i in range(lines_to_show):
            text, col = subdomains[i]
            draw.text((450, y), text, fill=col, font=f9)
            y += 16

        # Status text
        recon_status = "PASSIVE RECON" if frame < 100 else "ACTIVE RECON"
        draw.text((870, 360), f"[{recon_status}]", fill='#76B900' if frame < 100 else '#ef4444', font=f11)
        draw.text((870, 376), f"Phase: {'Discover' if frame < 50 else 'Map' if frame < 100 else 'Enumerate'}", fill='#999', font=f9)

        # Ethical check badge
        draw.rectangle([870, 420, W-20, 440], fill='#111', outline='#333', width=1)
        draw.text((880, 424), "🔒 ETHICAL CHECK: Target authorized", fill='#60a5fa', font=f9)

        frames.append(img)

    frames[0].save(
        'recon-shadowforge.gif',
        save_all=True,
        append_images=frames[1:],
        duration=int(1000/FPS),
        loop=0,
        optimize=True
    )
    print("GIF saved: recon-shadowforge.gif")


if __name__ == "__main__":
    main()
