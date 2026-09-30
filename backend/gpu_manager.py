from models import GPU


def create_gpus(count=3, capacity=8):
    """Software-simulated GPUs (no NVIDIA hardware needed)."""
    return [GPU(id=i + 1, capacity=capacity) for i in range(count)] 