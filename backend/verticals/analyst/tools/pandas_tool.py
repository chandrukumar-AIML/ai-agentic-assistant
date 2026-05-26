# backend/verticals/analyst/tools/pandas_tool.py
"""
Pandas code execution tool for Data Analyst agent.
Runs data analysis code in a restricted sandbox.
Returns JSON-serialisable results + summary stats.
"""
import asyncio
import logging
import json
from io import StringIO

logger = logging.getLogger(__name__)

ALLOWED_IMPORTS = {
    "pandas",   "numpy",    "json",
    "datetime", "math",     "statistics",
    "re",       "collections", "itertools",
}

PANDAS_SANDBOX_CODE = """
import pandas as pd
import numpy as np
import json
import math
import statistics
from datetime import datetime, timedelta
from collections import Counter

# Data is pre-loaded as 'df' if provided
{user_code}
"""


async def run_pandas_analysis(
    code:      str,
    data_json: str | None = None,   # JSON string of data to analyse
) -> dict:
    """
    Run pandas analysis code in a restricted environment.
    Returns: {"output": str, "summary": dict, "error": str | None}
    """
    import sys
    from io import StringIO
    import contextlib

    # Pre-load data as DataFrame if provided
    setup_code = ""
    if data_json:
        try:
            import pandas as pd
            import json as _json
            data = _json.loads(data_json)
            if isinstance(data, list):
                df_str = f"df = pd.DataFrame({data_json})"
                setup_code = df_str + "\n"
        except Exception:
            pass

    full_code = f"""
import pandas as pd
import numpy as np
import json
import math
from datetime import datetime
{setup_code}
{code}
"""
    output_buf = StringIO()
    result     = {}
    error      = None

    def _run():
        local_vars  = {}
        global_vars = {
            "__builtins__": {
                "print": print, "len": len, "range": range, "list": list,
                "dict": dict, "str": str, "int": int, "float": float,
                "bool": bool, "sum": sum, "min": min, "max": max,
                "round": round, "abs": abs, "sorted": sorted,
                "enumerate": enumerate, "zip": zip, "map": map,
                "isinstance": isinstance, "type": type,
            }
        }
        import pandas as pd
        import numpy as np
        global_vars.update({"pd": pd, "np": np, "json": __import__("json"),
                            "math": __import__("math"), "datetime": __import__("datetime").datetime})

        if setup_code:
            exec(setup_code, global_vars, local_vars)   # noqa: S102

        buf = StringIO()
        import contextlib
        with contextlib.redirect_stdout(buf):
            exec(full_code, global_vars, local_vars)    # noqa: S102

        output = buf.getvalue()

        # Extract DataFrame stats if 'df' in scope
        df_summary = {}
        if "df" in local_vars and hasattr(local_vars["df"], "shape"):
            df = local_vars["df"]
            try:
                if df.empty:  # FIXED: check for empty DataFrame before describe to avoid silent failure
                    df_summary = {"shape": df.shape, "columns": list(df.columns), "dtypes": {}, "empty": True}
                else:
                    df.describe(include="all")
                    df_summary = {
                        "shape":    df.shape,
                        "columns":  list(df.columns),
                        "dtypes":   {k: str(v) for k, v in df.dtypes.items()},
                    }
            except Exception as _df_err:  # FIXED: was bare `except Exception: pass` with no logging
                import logging as _logging
                _logging.getLogger(__name__).warning(f"DataFrame summary extraction failed: {_df_err}")

        return output, df_summary

    try:
        output, summary = await asyncio.wait_for(
            asyncio.to_thread(_run),
            timeout=30.0,
        )
        return {"output": output, "summary": summary, "error": None}
    except asyncio.TimeoutError:
        return {"output": "", "summary": {}, "error": "Analysis timed out (30s)"}
    except Exception as e:
        return {"output": "", "summary": {}, "error": str(e)[:300]}