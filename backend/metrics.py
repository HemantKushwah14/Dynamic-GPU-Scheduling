from task_manager import count_by_status


def wastage(gpus):
    total = sum(g.capacity for g in gpus)
    unused = sum(g.available for g in gpus)
    return {"unused": unused, "total": total,
            "overall": round(unused / total * 100, 1),
            "per_gpu": {g.id: round(g.available / g.capacity * 100, 1) for g in gpus}}


def summary(sim):
    cnt = count_by_status(sim.tasks)
    total = sum(g.capacity for g in sim.gpus)
    used = sum(g.used for g in sim.gpus)
    if sim.stage == 5:          # projected (dry run), before committing
        w = sim.projected
    elif sim.stage >= 6:        # actual, after allocation
        w = wastage(sim.gpus)
    else:
        w = None
    return {
        "total_gpus": len(sim.gpus),
        "available_gpus": sum(g.available > 0 for g in sim.gpus),
        "total_capacity": total, "used_capacity": used,
        "available_capacity": total - used,
        "utilization": round(used / total * 100, 1) if total else 0,
        "waiting": cnt["WAITING"], "running": cnt["RUNNING"],
        "completed": cnt["COMPLETED"],
        "wastage": w,
    }