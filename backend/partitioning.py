from models import Partition


def configure_partitions(gpus, size=4):
    """Split each GPU into simulated partitions of 'size' units (A, B, ...)."""
    for gpu in gpus:
        gpu.partitions = []
        left, i = gpu.capacity, 0
        while left > 0:
            cap = min(size, left)
            label = chr(65 + i)
            gpu.partitions.append(Partition(f"GPU{gpu.id}-{label}", label, gpu.id, cap))
            left -= cap
            i += 1
    return [p for g in gpus for p in g.partitions]