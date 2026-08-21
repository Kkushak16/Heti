import json
import os
from typing import List, Dict, Any

def generate_audit_dashboard_html(audit_log_path: str = "audit_log.jsonl", output_html_path: str = "audit_dashboard.html"):
    """Generates a standalone lightweight HTML audit log dashboard."""
    entries = []
    if os.path.exists(audit_log_path):
        with open(audit_log_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        entries.append(json.loads(line))
                    except Exception:
                        pass

    # Reverse entries to show newest events first
    entries.reverse()

    rows = []
    for entry in entries:
        status_color = "#10b981" if entry.get("status") == "SUCCESS" else ("#f59e0b" if "CANCELLED" in entry.get("status", "") else "#ef4444")
        rows.append(f"""
        <tr>
            <td style="padding: 10px; border-bottom: 1px solid #334155; font-size: 13px;">{entry.get("timestamp")}</td>
            <td style="padding: 10px; border-bottom: 1px solid #334155; font-weight: bold; color: #38bdf8;">{entry.get("tool_name")}</td>
            <td style="padding: 10px; border-bottom: 1px solid #334155;"><span style="background: #1e293b; padding: 4px 8px; border-radius: 4px; font-size: 12px; border: 1px solid #475569;">{entry.get("permission")}</span></td>
            <td style="padding: 10px; border-bottom: 1px solid #334155; color: {status_color}; font-weight: bold;">{entry.get("status")}</td>
            <td style="padding: 10px; border-bottom: 1px solid #334155; font-family: monospace; font-size: 12px; color: #94a3b8;">{json.dumps(entry.get("args"))}</td>
        </tr>
        """)

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Heti Security Audit Dashboard</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #0f172a; color: #f8fafc; margin: 0; padding: 20px; }}
        .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #334155; padding-bottom: 15px; margin-bottom: 20px; }}
        h1 {{ margin: 0; color: #38bdf8; font-size: 24px; }}
        .badge {{ background: #0284c7; padding: 6px 12px; border-radius: 20px; font-size: 13px; font-weight: bold; }}
        table {{ width: 100%; border-collapse: collapse; background: #1e293b; border-radius: 8px; overflow: hidden; }}
        th {{ background: #0f172a; text-align: left; padding: 12px; border-bottom: 2px solid #334155; color: #94a3b8; font-size: 13px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔒 Heti Agent Security & Tool Audit Trail</h1>
        <div class="badge">Total Events: {len(entries)}</div>
    </div>
    <table>
        <thead>
            <tr>
                <th>Timestamp (UTC)</th>
                <th>Tool Name</th>
                <th>Permission Level</th>
                <th>Status</th>
                <th>Arguments</th>
            </tr>
        </thead>
        <tbody>
            {"".join(rows) if rows else '<tr><td colspan="5" style="padding: 20px; text-align: center; color: #64748b;">No audit log events found.</td></tr>'}
        </tbody>
    </table>
</body>
</html>
"""

    with open(output_html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f" 📊 Audit Dashboard HTML generated at: {os.path.abspath(output_html_path)}")

if __name__ == "__main__":
    generate_audit_dashboard_html()
