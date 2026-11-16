"""Execute originals unchanged in a fresh project-venv kernel per notebook."""
import base64
import hashlib
import json
import os
from pathlib import Path
import queue
import sys
import time

from jupyter_client import KernelManager

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "audit"
os.environ["MPLCONFIGDIR"] = "/private/tmp/coffee-audit-matplotlib"
os.environ["IPYTHONDIR"] = "/private/tmp/coffee-audit-ipython"
os.environ["JUPYTER_RUNTIME_DIR"] = "/private/tmp/coffee-audit-jupyter"
for key in ("MPLCONFIGDIR", "IPYTHONDIR", "JUPYTER_RUNTIME_DIR"):
    Path(os.environ[key]).mkdir(parents=True, exist_ok=True)


def execute(client, source, timeout=180):
    mid = client.execute(source, store_history=True, stop_on_error=True)
    outputs = []
    count = None
    deadline = time.monotonic() + timeout
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("Cell exceeded timeout")
        try:
            msg = client.get_iopub_msg(timeout=min(remaining, 10))
        except queue.Empty:
            continue
        if msg.get("parent_header", {}).get("msg_id") != mid:
            continue
        kind, content = msg["msg_type"], msg["content"]
        if kind == "status" and content["execution_state"] == "idle":
            break
        if kind == "execute_input":
            count = content["execution_count"]
        elif kind in ("stream", "display_data", "execute_result", "error"):
            output = {"output_type": kind}
            keys = {
                "stream": ("name", "text"),
                "display_data": ("data", "metadata"),
                "execute_result": ("data", "metadata", "execution_count"),
                "error": ("ename", "evalue", "traceback"),
            }[kind]
            output.update({key: content[key] for key in keys})
            outputs.append(output)
        elif kind == "clear_output":
            outputs.clear()
    return count, outputs


results = []
for path in sorted((ROOT / "notebook").glob("*.ipynb")):
    notebook = json.loads(path.read_text())
    original_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    manager = KernelManager(connection_file=str(OUT / f".{path.stem}-kernel.json"))
    manager.kernel_spec.argv = [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"]
    started = time.monotonic()
    manager.start_kernel(cwd=str(ROOT / "notebook"), env=dict(os.environ))
    client = manager.client()
    client.start_channels()
    result = {"notebook": path.name, "sha256": original_hash, "cells": [], "errors": []}
    try:
        client.wait_for_ready(timeout=60)
        # Standard notebook frontends enable inline plotting before user cells.
        execute(client, "%matplotlib inline\nimport sys\nprint(sys.executable)")
        for i, cell in enumerate(notebook["cells"], 1):
            if cell["cell_type"] != "code":
                continue
            source = "".join(cell.get("source", []))
            cell["outputs"] = []
            cell["execution_count"] = None
            if not source.strip():
                continue
            count, outputs = execute(client, source)
            cell["execution_count"] = count
            cell["outputs"] = outputs
            errors = [o for o in outputs if o["output_type"] == "error"]
            result["cells"].append({"cell": i, "execution_count": count, "errors": len(errors)})
            result["errors"].extend({"cell": i, **o} for o in errors)
            for j, output in enumerate(outputs):
                png = output.get("data", {}).get("image/png")
                if png:
                    if isinstance(png, list):
                        png = "".join(png)
                    (OUT / "charts" / f"{path.stem}-cell-{i:02d}-{j}.png").write_bytes(base64.b64decode(png))
        # Reconcile the actual completed kernel state with independent workbook totals.
        common_probe = f'''
import json as _json
from pathlib import Path as _Path
_audit = _Path({str(OUT)!r})
_expected = _json.loads((_audit / "verification_results.json").read_text())
assert len(df) == _expected["rows"]
assert df["transaction_id"].nunique() == _expected["transaction_ids"]
assert df["transaction_qty"].sum() == _expected["total_units"]
'''
        probes = {
            "01_exploration.ipynb": '''
assert quality_summary["Issues Found"].sum() == 0
''',
            "02_sales_analysis.ipynb": '''
assert abs(total_combined_revenue - float(_expected["total_revenue_decimal"])) < 1e-6
assert abs(average_transaction_value - 698812.33 / 149116) < 1e-10
for _name, _series in [("detail", products_by_revenue), ("category", revenue_by_category["revenue"])]:
    _ref = pd.read_csv(_audit / f"revenue_by_{_name}.csv", index_col=0)["revenue"]
    pd.testing.assert_series_equal(_series.sort_index(), _ref.sort_index(), check_names=False, check_dtype=False, atol=1e-6, rtol=0)
_ref = pd.read_csv(_audit / "monthly_metrics.csv", index_col=0)["revenue"]
assert all(abs(by_month.loc[pd.Period(k)] - v) < 1e-6 for k,v in _ref.items())
_ref = pd.read_csv(_audit / "weekday_metrics.csv", index_col=0)["total_revenue"]
pd.testing.assert_series_equal(by_weekday.sort_index(), _ref.sort_index(), check_names=False, check_dtype=False, atol=1e-6, rtol=0)
_hourref = pd.read_csv(_audit / "hourly_metrics.csv")
assert store_hour.set_index(["store_location", "time_of_day"])["transactions"].to_dict() == _hourref.set_index(["store_location", "hour"])["transactions"].to_dict()
assert by_hour.to_dict() == _hourref.groupby("hour")["units"].sum().to_dict()
pd.testing.assert_series_equal(rev_by_hour.sort_index(), _hourref.groupby("hour")["revenue"].sum().sort_index(), check_names=False, check_dtype=False, atol=1e-6, rtol=0)
''',
            "03_visualization.ipynb": '''
_ref = pd.read_csv(_audit / "monthly_metrics.csv", index_col=0)["revenue"]
assert all(abs(total_revenue_monthly.loc[pd.Period(k)] - v) < 1e-6 for k,v in _ref.items())
_ref = pd.read_csv(_audit / "store_metrics.csv", index_col=0)["revenue"]
pd.testing.assert_series_equal(revenue_by_location.sort_index(), _ref.sort_index(), check_names=False, check_dtype=False, atol=1e-6, rtol=0)
_ref = pd.read_csv(_audit / "revenue_by_type.csv", index_col=0)["revenue"]
pd.testing.assert_series_equal(revenue_by_product.sort_index(), _ref.sort_index(), check_names=False, check_dtype=False, atol=1e-6, rtol=0)
_ref = pd.read_csv(_audit / "hourly_metrics.csv")
assert store_hour.set_index(["store_location", "time_of_day"])["transactions"].to_dict() == _ref.set_index(["store_location", "hour"])["transactions"].to_dict()
_ref = pd.read_csv(_audit / "revenue_by_category.csv", index_col=0)["revenue"]
pd.testing.assert_series_equal(temp["revenue"].sort_index(), _ref.sort_index(), check_names=False, check_dtype=False, atol=1e-6, rtol=0)
pd.testing.assert_series_equal(temp["percentage"].sort_index(), (_ref/_ref.sum()*100).round(2).sort_index(), check_names=False, check_dtype=False)
''',
        }
        if (OUT / "verification_results.json").exists():
            _, probe_outputs = execute(client, common_probe + probes[path.name] + '\nprint("Kernel-state reconciliation passed")')
            result["reconciliation_outputs"] = probe_outputs
            result["errors"].extend({"cell": "audit reconciliation", **o} for o in probe_outputs if o["output_type"] == "error")
        (OUT / "executed" / path.name).write_text(json.dumps(notebook, indent=1) + "\n")
    finally:
        client.stop_channels()
        manager.shutdown_kernel(now=True)
    result["seconds"] = round(time.monotonic() - started, 2)
    result["original_unchanged"] = original_hash == hashlib.sha256(path.read_bytes()).hexdigest()
    results.append(result)
    print(json.dumps(result), flush=True)
(OUT / "execution_results.json").write_text(json.dumps(results, indent=2) + "\n")
if any(r["errors"] for r in results):
    sys.exit(1)
