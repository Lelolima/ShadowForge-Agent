#!/usr/bin/env python3
"""Generate animated GIF for Step 6: Report Generation."""
from PIL import Image, ImageDraw, ImageFont
import math


def main():
    W, H = 1200, 700
    FPS = 10
    TOTAL = 220

    try:
        f11 = ImageFont.truetype("cour.ttf", 11)
        f9 = ImageFont.truetype("cour.ttf", 9)
        f13 = ImageFont.truetype("courbd.ttf", 13)
        f16 = ImageFont.truetype("courbd.ttf", 16)
        f20 = ImageFont.truetype("courbd.ttf", 20)
    except OSError:
        f11 = f9 = f13 = f16 = f20 = ImageFont.load_default()

    frames = []

    for frame in range(TOTAL):
        img = Image.new('RGB', (W, H), '#050505')
        draw = ImageDraw.Draw(img)

        # Title
        draw.rectangle([0, 0, W, 40], fill='#0a0a0a', outline='#222', width=1)
        draw.text((20, 8), "STEP 6/6: REPORT GENERATION", fill='#76B900', font=f20)
        draw.text((W-280, 12), "ShadowForge Ethical Hacking Report", fill='#444', font=f11)

        # Progress
        progress = min(frame / TOTAL, 1.0)
        bar_w = int((W - 40) * progress)
        draw.rectangle([20, H-30, W-20, H-10], outline='#333', width=1, fill='#111')
        if bar_w > 0:
            draw.rectangle([20, H-30, 20+bar_w, H-10], fill='#1a3000', outline='#76B900', width=1)
        draw.text((W//2 - 50, H-27), f"Generating Report... {int(progress*100)}%", fill='#76B900', font=f11)

        # Left: Executive Summary
        draw.rectangle([20, 50, 450, 250], fill='#0a0a0a', outline='#222', width=1)
        draw.rectangle([20, 50, 450, 75], fill='#111')
        draw.text((30, 55), "Executive Summary", fill='#76B900', font=f16)

        summary_lines = [
            ("Target: 192.168.1.0/24", '#fff'),
            ("Scope: Authorized penetration test", '#999'),
            ("Date: 2026-05-25", '#999'),
            ("", '#000'),
            ("Findings:", '#76B900'),
            ("  SQL Injection: 1 (Critical)", '#ef4444'),
            ("  XSS: 2 (High)", '#f97316'),
            ("  Weak Passwords: 3 (Medium)", '#fbbf24'),
            ("  Open Ports: 8 (Info)", '#22c55e'),
            ("", '#000'),
            ("Overall Risk: HIGH", '#ef4444'),
            ("Remediation Priority: Immediate", '#fbbf24'),
        ]

        lines_show = min(frame // 17, len(summary_lines))
        y = 80
        for i in range(lines_show):
            line, col = summary_lines[i]
            draw.text((30, y), line, fill=col, font=f11)
            y += 16

        # Right top: Risk Matrix
        draw.rectangle([470, 50, W-20, 250], fill='#0a0a0a', outline='#222', width=1)
        draw.rectangle([470, 50, W-20, 75], fill='#111')
        draw.text((480, 55), "Risk Matrix", fill='#76B900', font=f16)

        # Matrix grid 5x5
        cell_w, cell_h = 60, 30
        for row in range(5):
            for col in range(5):
                x = 480 + col * cell_w
                y_pos = 85 + row * cell_h
                # Color based on risk level
                risk = (4-row) + col
                if risk >= 7:
                    color = '#ef4444'
                elif risk >= 5:
                    color = '#f97316'
                elif risk >= 3:
                    color = '#fbbf24'
                else:
                    color = '#22c55e'
                draw.rectangle([x, y_pos, x+cell_w-2, y_pos+cell_h-2], fill=color if frame > 30 + (row*5+col)*2 else '#111', outline='#333', width=1)

        # Labels
        labels = [("Low", '#22c55e'), ("Medium", '#fbbf24'), ("High", '#ef4444'), ("Critical", '#dc2626')]
        for i, (label, col) in enumerate(labels):
            draw.rectangle([480, 230 + i*20, 495, 245 + i*20], fill=col)
            draw.text((500, 230 + i*20), label, fill=col, font=f9)

        # Middle: Detailed Findings
        draw.rectangle([20, 270, W-20, 520], fill='#0a0a0a', outline='#222', width=1)
        draw.rectangle([20, 270, W-20, 295], fill='#111')
        draw.text((30, 275), "Detailed Findings", fill='#76B900', font=f16)

        findings = [
            ("1", "SQL Injection", "Critical", "7.5", "192.168.1.10:80", "CVE-2026-XXXX", "Use parameterized queries"),
            ("2", "Cross-Site Scripting (XSS)", "High", "6.2", "192.168.1.10:80", "CVE-2026-YYYY", "Sanitize user inputs"),
            ("3", "Command Injection", "High", "7.1", "192.168.1.10:80", "CVE-2026-ZZZZ", "Validate all inputs"),
            ("4", "Weak Passwords", "Medium", "5.3", "192.168.1.10:22", "", "Enforce strong password policy"),
            ("5", "Missing HttpOnly Flag", "Medium", "4.1", "192.168.1.10:80", "", "Set HttpOnly on session cookies"),
        ]

        # Headers
        headers = ["#", "Vulnerability", "Severity", "CVSS", "Asset", "CVE", "Recommendation"]
        header_xs = [30, 60, 260, 330, 390, 500, 600]
        for i, h in enumerate(headers):
            # x = header_xs[i] if i < len(header_xs) else 30 + i*100
            draw.text((header_xs[i] if i < len(header_xs) else 30+i*100, 300), h, fill='#76B900', font=f11)

        lines_to_show = min(max(0, (frame - 60) // 20), len(findings))
        for row_idx in range(lines_to_show):
            y = 320 + row_idx * 25
            f = findings[row_idx]
            draw.text((30, y), f[0], fill='#999', font=f9)
            draw.text((60, y), f[1][:25], fill='#fff', font=f9)
            sev_colors = {'Critical': '#ef4444', 'High': '#f97316', 'Medium': '#fbbf24', 'Low': '#22c55e'}
            draw.text((260, y), f[2], fill=sev_colors.get(f[2], '#999'), font=f9)
            draw.text((330, y), f[3], fill='#76B900', font=f9)
            draw.text((390, y), f[4], fill='#999', font=f9)
            draw.text((500, y), f[5] or "N/A", fill='#999', font=f9)
            draw.text((600, y), f[6][:30], fill='#60a5fa', font=f9)

        # Right: Remediation timeline
        draw.rectangle([W-260, 270, W-20, 520], fill='#0a0a0a', outline='#222', width=1)
        draw.rectangle([W-260, 270, W-20, 295], fill='#111')
        draw.text((W-250, 275), "Remediation", fill='#76B900', font=f16)

        timeline = [
            ("Immediate (0-7 days)", '#ef4444', 3),
            ("  Fix SQL Injection", '#999', 3),
            ("  Patch CVE-2026-XXXX", '#999', 3),
            ("", '#000', 0),
            ("Short-term (7-30 days)", '#f97316', 2),
            ("  Fix XSS vulnerabilities", '#999', 2),
            ("  Update nginx version", '#999', 2),
            ("", '#000', 0),
            ("Medium-term (1-3 months)", '#fbbf24', 2),
            ("  Implement WAF rules", '#999', 2),
            ("  Security code review", '#999', 2),
            ("", '#000', 0),
            ("Long-term (3-6 months)", '#76B900', 2),
            ("  Security architecture review", '#999', 2),
            ("  Continuous monitoring", '#999', 2),
        ]

        t_show = min(max(0, (frame - 80) // 15), len(timeline))
        y_t = 300
        for i in range(t_show):
            line, col, _ = timeline[i]
            draw.text((W-250, y_t), line, fill=col, font=f9)
            y_t += 14

        # Bottom: Report Export
        draw.rectangle([20, 540, W-20, 640], fill='#0a0a0a', outline='#222', width=1)
        draw.rectangle([20, 540, W-20, 565], fill='#111')
        draw.text((30, 545), "Report Export", fill='#76B900', font=f16)

        exports = [
            ("PDF Report", "report_shadowforge.pdf", '#ef4444', "Critical vulnerabilities detailed"),
            ("HTML Report", "report_shadowforge.html", '#60a5fa', "Interactive dashboard with charts"),
            ("JSON Data", "report_shadowforge.json", '#fbbf24', "Machine-readable findings"),
            ("CSV Export", "report_shadowforge.csv", '#22c55e', "Spreadsheet format for tracking"),
        ]

        for i, (fmt, filename, color, desc) in enumerate(exports):
            x = 30 + i * 290
            draw.rectangle([x, 570, x+270, 615], fill='#111', outline='#333', width=1)
            draw.text((x+10, 575), fmt, fill='#fff', font=f11)
            draw.text((x+10, 590), filename, fill=color, font=f9)
            draw.text((x+10, 602), desc, fill='#666', font=f9)

        # Status
        if frame > 180:
            draw.rectangle([20, 650, W-20, 670], fill='#111', outline='#333', width=1)
            draw.text((30, 654), "✓ Report generation complete. Authorized test concluded.", fill='#22c55e', font=f11)

        frames.append(img)

    frames[0].save(
        'report-shadowforge.gif',
        save_all=True,
        append_images=frames[1:],
        duration=int(1000/FPS),
        loop=0,
        optimize=True
    )
    print("GIF saved: report-shadowforge.gif")


if __name__ == "__main__":
    main()
