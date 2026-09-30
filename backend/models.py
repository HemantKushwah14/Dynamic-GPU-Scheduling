from dataclasses import dataclass, field, asdict


@dataclass
class Task:
    id: str
    gpu: int            # GPU requirement (units)
    arrival: int
    exec_time: int
    status: str = "WAITING"   # WAITING | RUNNING | COMPLETED
    group: str = None

    def to_dict(self):
        return asdict(self)


@dataclass
class Group:
    id: str
    tasks: list
    total: int

    def to_dict(self):
        return asdict(self)


@dataclass
class Partition:
    id: str
    label: str
    gpu_id: int
    capacity: int
    used: int = 0
    tasks: list = field(default_factory=list)
    groups: list = field(default_factory=list)

    @property
    def available(self):
        return self.capacity - self.used

    def to_dict(self):
        d = asdict(self)
        d["available"] = self.available
        return d


@dataclass
class GPU:
    id: int
    capacity: int
    partitions: list = field(default_factory=list)

    @property
    def used(self):
        return sum(p.used for p in self.partitions)

    @property
    def available(self):
        return self.capacity - self.used

    @property
    def utilization(self):
        return round(self.used / self.capacity * 100, 1)

    @property
    def tasks(self):
        return [t for p in self.partitions for t in p.tasks]

    def to_dict(self):
        return {
            "id": self.id, "capacity": self.capacity, "used": self.used,
            "available": self.available, "utilization": self.utilization,
            "wastage": round(100 - self.utilization, 1), "tasks": self.tasks,
            "partitions": [p.to_dict() for p in self.partitions],
        }