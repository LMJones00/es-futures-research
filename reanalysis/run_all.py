"""Runs the September 2026 re-analysis end to end.

Needs clean.csv and cleaning.csv in the project root (pipeline outputs) and internet access for
stage 04 (SPY and VIX daily history via yfinance). Writes intermediate tables to reanalysis/_out/
(gitignored, *.csv) and the full text report to reanalysis/_out/report.txt.

    python reanalysis/run_all.py
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "_out")
os.makedirs(OUT, exist_ok=True)
ENV = dict(os.environ, PYTHONIOENCODING="utf-8")

stages = sorted(f for f in os.listdir(HERE) if f[:2].isdigit() and f.endswith(".py"))
with open(os.path.join(OUT, "report.txt"), "w", encoding="utf-8") as report:
    for name in stages:
        banner = "\n\n" + "#" * 100 + "\n# " + name + "\n" + "#" * 100 + "\n"
        print(banner)
        report.write(banner)
        result = subprocess.run(
            [sys.executable, os.path.join(HERE, name)],
            capture_output=True, text=True, env=ENV, encoding="utf-8",
        )
        print(result.stdout)
        report.write(result.stdout)
        if result.returncode != 0:
            print(result.stderr)
            report.write(result.stderr)
            print("!! " + name + " failed; stopping.")
            break
print("done ->", os.path.join(OUT, "report.txt"))
