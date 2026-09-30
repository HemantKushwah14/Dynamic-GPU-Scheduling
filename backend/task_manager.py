import json, os
from models import Task

DATA = os.path.join(os.path.dirname(__file__), "data", "sample_tasks.json")


def read_rows(path=DATA):
    """Sample JSON -> editable rows used by the website."""
    with open(path) as f:
        return [{"gpu": r["gpu_requirement"], "arrival": r["arrival_time"],
                 "exec_time": r["execution_time"]} for r in json.load(f)]


def clean_rows(rows, max_gpu):
    """Validate values typed on the website. IDs are renumbered T1..Tn."""
    if not rows:
        raise ValueError("Add at least one task.")
    if len(rows) > 30:
        raise ValueError("Maximum 30 tasks.")
    out = []
    for i, r in enumerate(rows, 1):
        try:
            g, a, e = int(r["gpu"]), int(r["arrival"]), int(r["exec_time"])
        except (KeyError, TypeError, ValueError):
            raise ValueError(f"T{i}: all values must be whole numbers.")
        if not 1 <= g <= max_gpu:
            raise ValueError(f"T{i}: GPU requirement must be between 1 and {max_gpu} (partition size).")
        if a < 0 or e < 1:
            raise ValueError(f"T{i}: arrival must be >= 0 and execution time >= 1.")
        out.append({"gpu": g, "arrival": a, "exec_time": e})
    return out


def load_tasks(rows):
    return [Task(f"T{i}", r["gpu"], r["arrival"], r["exec_time"])
            for i, r in enumerate(rows, 1)]


def count_by_status(tasks):
    return {s: sum(t.status == s for t in tasks)
            for s in ("WAITING", "RUNNING", "COMPLETED")}