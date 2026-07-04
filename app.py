"""Root entrypoint so `streamlit run app.py` works. Delegates to streamlit/app.py.

On Streamlit Community Cloud you may set the main file path to either `app.py`
(this launcher) or `streamlit/app.py` directly.
"""
import runpy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
runpy.run_path(str(ROOT / "streamlit" / "app.py"), run_name="__main__")
