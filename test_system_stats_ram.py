import sys
import os

sys.path.insert(0, r"d:\Antigravity")

from Heti.tools.system_tools import SystemStatsTool
from Heti.agent.core_agent import HetiAgent

def test_system_stats_and_ram_guard():
    print("--- 1. Testing Enhanced SystemStatsTool (CPU/RAM/Disk/Battery) ---")
    stats_tool = SystemStatsTool()
    res = stats_tool.execute(detailed=True)
    print("System Stats Output:")
    print(res)

    assert "cpu_percent" in res, "Missing cpu_percent in stats!"
    assert "memory" in res and "free_mb" in res["memory"], "Missing memory free_mb in stats!"
    assert "disk" in res, "Missing disk metrics in stats!"
    assert "battery" in res, "Missing battery metric entry in stats!"

    print("\n--- 2. Testing Lite Loop RAM Headroom Check (< 500MB Limit) ---")
    agent = HetiAgent()

    # Test normal RAM check (should pass on standard dev machines with >500MB free)
    warning_normal = agent._check_ram_headroom(min_free_mb=500.0)
    print("Normal RAM check result:", warning_normal if warning_normal else "PASS (sufficient RAM available)")

    # Test simulated low RAM check (trigger with high threshold e.g. 1,000,000 MB)
    warning_triggered = agent._check_ram_headroom(min_free_mb=1000000.0)
    print("Simulated low RAM trigger result:", warning_triggered)

    assert warning_triggered is not None and "RAM Headroom Warning" in warning_triggered, "RAM guard failed to block when free RAM is insufficient!"

    print("\n✅ SystemStatsTool and Lite RAM-headroom OOM Guard verified successfully!")

if __name__ == "__main__":
    test_system_stats_and_ram_guard()
