import copy
from task_manager import read_rows, clean_rows, load_tasks
from gpu_manager import create_gpus
from grouping import group_tasks, analyze_groups
from partitioning import configure_partitions
from allocation import allocate
import metrics

DEFAULT_CFG = {"gpu_count": 3, "capacity": 8, "partition_size": 4}

STAGES = [
    ("Workload", "Tasks (GPU requirement, arrival, execution time, state) and the simulated GPUs are loaded. All tasks start WAITING."),
    ("Task Grouping", "Compatible tasks are grouped according to their GPU resource requirements so that available GPU resources can be utilized efficiently."),
    ("Resource Analysis", "Each group's total requirement is compared with available GPU capacity to check feasibility and remaining capacity."),
    ("GPU Partitioning", "Available GPU capacity is divided into simulated partitions that can accommodate the grouped workloads."),
    ("Resource Wastage", "Unused capacity is calculated (Wastage % = unused / total x 100) for a dry-run allocation, per GPU and overall."),
    ("Initial Allocation", "Task groups are assigned to feasible GPU partitions without exceeding available capacity."),
]


class Simulation:
    def __init__(self):
        self.rows = read_rows()
        self.cfg = dict(DEFAULT_CFG)
        self.reset()

    def reset(self):
        """Clears results only. Your edited tasks/settings are kept."""
        self.tasks, self.gpus, self.groups = [], [], []
        self.analysis, self.allocations, self.projected = [], [], None
        self.stage, self.paused = 0, False

    # ---- values edited on the website ----
    def configure(self, rows, cfg):
        try:
            n, cap, ps = int(cfg["gpu_count"]), int(cfg["capacity"]), int(cfg["partition_size"])
        except (KeyError, TypeError, ValueError):
            raise ValueError("GPU settings must be whole numbers.")
        if not 1 <= n <= 6:
            raise ValueError("Number of GPUs must be between 1 and 6.")
        if not 2 <= cap <= 32:
            raise ValueError("Capacity per GPU must be between 2 and 32.")
        if not 1 <= ps <= cap:
            raise ValueError("Partition size must be between 1 and the GPU capacity.")
        self.rows = clean_rows(rows, ps)      # validate before changing anything
        self.cfg = {"gpu_count": n, "capacity": cap, "partition_size": ps}
        self.reset()
        self.load_workload()
        self.initialize_gpus()

    # ---- Phase 1 ----
    def load_workload(self):
        if self.stage > 1:
            self.reset()
        self.tasks = load_tasks(self.rows)
        self._ready()

    def initialize_gpus(self):
        if self.stage > 1:
            self.reset()
        self.gpus = create_gpus(self.cfg["gpu_count"], self.cfg["capacity"])
        self._ready()

    def _ready(self):
        if self.tasks and self.gpus and self.stage == 0:
            self.stage = 1

    # ---- one algorithm stage per call ----
    def step(self):
        if self.stage >= 6:
            return
        self.paused = False
        if self.stage == 0:
            if not self.tasks: self.load_workload()
            if not self.gpus: self.initialize_gpus()
            return
        self.stage += 1
        [None, None, self._grouping, self._analysis, self._partitioning,
         self._wastage, self._allocation][self.stage]()

    def _grouping(self):
        self.groups = group_tasks(self.tasks, self.cfg["partition_size"])

    def _analysis(self):
        self.analysis = analyze_groups(self.groups, self.gpus)

    def _partitioning(self):
        configure_partitions(self.gpus, self.cfg["partition_size"])

    def _wastage(self):
        g, t = copy.deepcopy(self.gpus), copy.deepcopy(self.tasks)
        allocate(self.groups, g, {x.id: x for x in t})
        self.projected = metrics.wastage(g)

    def _allocation(self):
        self.allocations = allocate(self.groups, self.gpus, {t.id: t for t in self.tasks})

    def run_phase1(self):
        while self.stage < 1:
            self.step()

    def run_phase2(self):
        self.run_phase1()
        while self.stage < 6:
            self.step()

    def state(self):
        name, expl = STAGES[max(self.stage, 1) - 1]
        return {
            "stage": self.stage, "stage_name": name, "explanation": expl,
            "stages": [s[0] for s in STAGES], "paused": self.paused,
            "config": {**self.cfg, "rows": self.rows},
            "tasks": [t.to_dict() for t in self.tasks],
            "gpus": [g.to_dict() for g in self.gpus],
            "groups": [g.to_dict() for g in self.groups],
            "partitions": [p.to_dict() for g in self.gpus for p in g.partitions],
            "analysis": self.analysis, "allocations": self.allocations,
            "metrics": metrics.summary(self),
        }