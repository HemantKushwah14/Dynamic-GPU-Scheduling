def allocate(groups, gpus, tasks_by_id):
    """
    Best-Fit allocation (never over-allocates):
    for each group (largest first) pick the partition with enough free capacity
    that leaves the LEAST space unused. Commit usage, mark tasks RUNNING,
    and record every decision.
    """
    decisions = []
    for g in sorted(groups, key=lambda g: -g.total):
        best = None
        for gpu in gpus:
            for p in gpu.partitions:
                if p.available >= g.total:
                    left = p.available - g.total
                    if best is None or left < best[0]:
                        best = (left, p)
        if best:
            p = best[1]
            p.used += g.total
            p.tasks += g.tasks
            p.groups.append(g.id)
            for tid in g.tasks:
                tasks_by_id[tid].status = "RUNNING"
            decisions.append({"group": g.id, "gpu": f"GPU {p.gpu_id}",
                              "partition": p.label, "required": g.total,
                              "unused": p.available, "status": "Allocated"})
        else:
            decisions.append({"group": g.id, "gpu": "-", "partition": "-",
                              "required": g.total, "unused": 0,
                              "status": "Waiting (no feasible partition)"})
    return decisions