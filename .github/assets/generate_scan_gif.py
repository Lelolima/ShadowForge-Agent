#!/usr/bin/env python3
"""Generate animated GIF for Step 4: Scanning & Enumeration."""
from PIL import Image, ImageDraw, ImageFont
import math
import random
random.seed(42)

def main():
    W, H = 1000, 550
    FPS = 10
    TOTAL = 180

    try:
        f11 = ImageFont.truetype("cour.ttf", 11)
        f9 = ImageFont.truetype("cour.ttf", 9)
        f14 = ImageFont.truetype("courbd.ttf", 14)
    except OSError:
        f11 = f9 = f14 = ImageFont.load_default()

    frames = []
    scan_ports = [22, 80, 443, 3306, 8080, 8443, 9000, 9200]

    for frame in range(TOTAL):
        img = Image.new('RGB', (W, H), '#050505')
        draw = ImageDraw.Draw(img)

        # Title
        draw.rectangle([0, 0, W, 30], fill='#0a0a0a', outline='#222', width=1)
        draw.text((10, 6), "STEP 4/6: SCANNING & ENUMERATION", fill='#76B900', font=f14)
        draw.text((W-180, 6), "Scan: 192.168.1.10", fill='#444', font=f9)

        # Progress bar
        progress = min(frame / TOTAL, 1.0)
        bar_w = int((W - 40) * progress)
        draw.rectangle([20, H-20, W-20, H-8], outline='#333', width=1, fill='#111')
        if bar_w > 0:
            draw.rectangle([20, H-20, 20 + bar_w, H-8], fill='#1a3000', outline='#76B900', width=1)
        draw.text((W//2 - 30, H-19), f"Scanning... {int(progress * 100)}%", fill='#76B900', font=f9)

        # Left: Port scan visualization
        draw.rectangle([20, 40, 420, 340], fill='#0a0a0a', outline='#333', width=1)
        draw.rectangle([20, 40, 420, 60], fill='#111')
        draw.text((30, 46), "Port Scan Visualization", fill='#76B900', font=f11)

        # 65k ports in grid
        ports_per_row = 64
        max_ports = 65 * 64  # ~4096 visible
        for i in range(max_ports):
            row = i // ports_per_row
            col = i % ports_per_row
            x = 30 + col * 6
            y = 68 + row * 5
            if y > 335:
                break

            # Animate scan
            scan_progress = frame * 30
            if i < scan_progress:
                # Discovered
                if i in [0, 79, 443, 3305, 8079, 8442, 8999, 9199]:  # Known ports
                    color = '#22c55e'  # Open
                    draw.rectangle([x-2, y-2, x+2, y+2], fill=color)
                elif i % 50 < 2:  # Random noise
                    draw.rectangle([x-2, y-2, x+2, y+2], fill='#ef4444')
                else:
                    draw.rectangle([x, y, x+2, y+2], fill='#333')
            else:
                draw.rectangle([x, y, x+2, y+2], fill='#111')

        # Status
        ports_scanned = min(frame * 22, 65535)
        draw.text((30, 315), f"Scanned: {ports_scanned:,} / 65,535", fill='#76B900', font=f11)
        open_ports = min(frame // 20, len(scan_ports))
        draw.text((30, 332), f"Open: {open_ports} | Closed: 65,{535-open_ports}", fill='#999', font=f9)

        # Middle: Detailed port results
        draw.rectangle([440, 40, 850, 340], fill='#0a0a0a', outline='#333', width=1)
        draw.rectangle([440, 40, 850, 60], fill='#111')
        draw.text((450, 46), "Service Enumeration", fill='#76B900', font=f11)

        port_results = [
            ("22/tcp   open    ssh          OpenSSH 8.9p1", '#22c55e'),
            ("   └─ Key Exchange: curve25519-sha256", '#999'),
            ("   └─ Auth: publickey,password", '#999'),
            ("", '#000'),
            ("80/tcp   open    http         nginx 1.18.0", '#22c55e'),
            ("   └─ Wappalyzer: React, Bootstrap", '#999'),
            ("   └─ CVE-2023-38408 (NVD)", '#fbbf24'),
            ("   └─ Robots.txt: /admin, /api/", '#999'),
            ("", '#000'),
            ("443/tcp  open    https        Apache/2.4.52", '#22c55e'),
            ("   └─ TLS: 1.2, 1.3", '#999'),
            ("   └─ Cipher: TLS_AES_256_GCM_SHA384", '#999'),
            ("", '#000'),
            ("3306/tcp open    mysql        MySQL 8.0.33", '#22c55e'),
            ("   └─ Version: 8.0.33-0ubuntu0.22.04.2", '#999'),
            ("   └─ No password policy enforced", '#ef4444'),
            ("", '#000'),
            ("8080/tcp open    http-proxy   Apache Tomcat/9.0.65", '#22c55e'),
            ("   └─ Manager: /manager/html", '#fbbf24'),
            ("   └─ Credentials: admin:admin (weak)", '#ef4444'),
        ]

        port_lines_to_show = min(frame // 9, len(port_results))
        y = 68
        for i in range(port_lines_to_show):
            line, col = port_results[i]
            draw.text((450, y), line, fill=col, font=f9)
            y += 13

        # Right: Vulnerability scan
        draw.rectangle([870, 40, W-20, 340], fill='#0a0a0a', outline='#333', width=1)
        draw.rectangle([870, 40, W-20, 60], fill='#111')
        draw.text((880, 46), "Vulnerability Scan", fill='#76B900', font=f11)

        vulns = [
            ("CVE-2023-38408", "Medium", "nginx < 1.22.0"),
            ("CVE-2022-42889", "High", "Apache Commons Text"),
            ("CVE-2024-20918", "Critical", "MySQL < 8.0.34"),
            ("CVE-2023-46604", "Critical", "Apache ActiveMQ"),
            ("", "", ""),
            ("Total CVEs: 4", "", ""),
            ("Critical: 2 | High: 1 | Medium: 1", "", ""),
            ("", "", ""),
            ("OWASP TOP 10:", "", ""),
            ("  A01 - Broken Access Control", "", ""),
            ("  A02 - Cryptographic Failures", "", ""),
            ("  A03 - Injection (SQLi)", "", ""),
        ]

        lines_to_show = min(frame // 14, len(vulns))
        y = 70
        for i in range(lines_to_show):
            if i < len(vulns):
                cve, sev, desc = vulns[i]
                col = '#999'
                if sev == "Critical":
                    col = '#ef4444'
                elif sev == "High":
                    col = '#f97316'
                elif sev == "Medium":
                    col = '#fbbf24'
                draw.text((880, y), f"{cve:20} {sev:8} {desc}", fill=col, font=f9)
                y += 16

        # Service fingerprint
        draw.rectangle([20, 360, 600, 500], fill='#0a0a0a', outline='#333', width=1)
        draw.rectangle([20, 360, 600, 380], fill='#111')
        draw.text((30, 366), "Banner Grabbing & Fingerprint", fill='#76B900', font=f11)

        banners = [
            ("Target: 192.168.1.10:80", '#fff'),
            ("HTTP/1.1 200 OK", '#76B900'),
            ("Server: nginx/1.18.0", '#999'),
            ("X-Powered-By: React/17.0.2", '#999'),
            ("Set-Cookie: session=abc123; HttpOnly", '#999'),
            ("", '#000'),
            ("SSL/TLS Scan:", '#76B900'),
            ("  Protocols: TLSv1.2, TLSv1.3", '#999'),
            ("  Cipher: TLS_AES_256_GCM_SHA384", '#999'),
            ("  Certificate: Valid (Expires 2027-01-15)", '#22c55e'),
        ]

        lines_to_show = min(frame // 16, len(banners))
        y = 390
        for i in range(lines_to_show):
            line, col = banners[i]
            draw.text((30, y), line, fill=col, font=f9)
            y += 14

        # Ethical badge
        draw.rectangle([620, 440, W-20, 460], fill='#111', outline='#333', width=1)
        draw.text((630, 444), "🔒 ETHICAL CHECK: Scan whitelisted targets only", fill='#60a5fa', font=f9)

        # Scan speed
        draw.text((620, 360), f"Scan rate: {min(frame * 2, 5000)} pkt/s", fill='#999', font=f11)
        draw.text((620, 378), f"Timeout: 2s | Threads: 100", fill='#999', font=f9)

        frames.append(img)

    frames[0].save(
        'scan-shadowforge.gif',
        save_all=True,
        append_images=frames[1:],
        duration=int(1000/FPS),
        loop=0,
        optimize=True
    )
    print("GIF saved: scan-shadowforge.gif")


if __name__ == "__main__":
    main()
