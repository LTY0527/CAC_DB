from pathlib import Path
import runpy


ROOT_DIR = Path(__file__).resolve().parents[2]


if __name__ == "__main__":
    runpy.run_path(str(ROOT_DIR / "CF-all.py"), run_name="__main__")
