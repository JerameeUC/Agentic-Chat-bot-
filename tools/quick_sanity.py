# /tools/quick_sanity.py
"""
Tiny sanity test for MBF helpers. Run from repo root or set PYTHONPATH.
"""
import sys, os
# Add repo root so 'mbf_bot' is importable if running directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from mbf_bot.skills import reverse_text, capabilities, normalize

print("caps:", capabilities())
print("reverse:", reverse_text("hello"))
print("cmd:", normalize("  Help  "))
