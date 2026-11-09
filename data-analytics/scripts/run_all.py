"""Run the whole data pipeline in order:  python scripts/run_all.py"""
import subprocess, sys
from pathlib import Path

here = Path(__file__).resolve().parent
steps = ["01_clean_crop_production.py", "02_clean_rainfall.py", "03_merge_yield_rainfall.py",
         "04_clean_mandi.py", "05_eda.py", "06_load_sql.py"]
for s in steps:
    print(f"\n########## {s}")
    if subprocess.run([sys.executable, str(here / s)], cwd=here).returncode != 0:
        sys.exit(f"Stopped: {s} failed")
print("\nAll done. Start the dashboard with:  python data-analytics/dashboard/app.py")
