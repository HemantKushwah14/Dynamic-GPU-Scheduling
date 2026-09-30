# GPU Resource Allocation Virtual Lab (Phase 1 + Phase 2)

Simulated GPU workload management, task grouping and initial allocation.
No NVIDIA hardware, database or Node.js required.

## Run
    cd backend
    pip install -r requirements.txt
    python app.py
Open http://127.0.0.1:5000

## Algorithm (viva summary)
1. Workload: load tasks (WAITING) + 3 simulated GPUs (8 units each)
2. Grouping: First-Fit Decreasing bin packing, group limit = partition size (4)
3. Analysis: group requirement vs available GPU capacity -> fits / remaining
4. Partitioning: each GPU split into Partition A (4) + Partition B (4)
5. Wastage: dry-run allocation; Wastage % = unused / total x 100
6. Allocation: Best-Fit partition (least leftover), no over-allocation; tasks -> RUNNING