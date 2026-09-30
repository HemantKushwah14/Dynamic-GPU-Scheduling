from models import Group


def group_tasks(tasks, limit):
    """
    First-Fit Decreasing bin packing.
    1. Sort tasks by GPU requirement (largest first).
    2. Put each task in the first group whose total stays <= limit.
    3. If none fits, open a new group.
    'limit' = largest partition size, so every group can fit one partition.
    """
    groups = []
    for t in sorted(tasks, key=lambda t: (-t.gpu, t.arrival)):
        target = next((g for g in groups if g.total + t.gpu <= limit), None)
        if target:
            target.tasks.append(t.id)
            target.total += t.gpu
        else:
            target = Group(f"G{len(groups) + 1}", [t.id], t.gpu)
            groups.append(target)
        t.group = target.id
    return groups


def analyze_groups(groups, gpus):
    """Resource analysis: does each group fit on some GPU?"""
    best_free = max(g.available for g in gpus)
    return [{
        "group": g.id, "num_tasks": len(g.tasks), "required": g.total,
        "available": best_free, "fits": g.total <= best_free,
        "remaining": best_free - g.total,
    } for g in groups]