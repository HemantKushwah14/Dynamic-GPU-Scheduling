# GPU Resource Allocation Virtual Lab (Phase 1 + Phase 2)

<img width="1920" height="1080" alt="Screenshot 2026-09-30 190541" src="https://github.com/user-attachments/assets/3a9055e9-6311-4a3e-a18a-4eda391d208e" />
<img width="1920" height="1080" alt="Screenshot 2026-09-30 190604" src="https://github.com/user-attachments/assets/083eafc0-aa62-46c3-bc2e-5e96b3d2fba0" />
<img width="1920" height="1080" alt="Screenshot 2026-09-30 190617" src="https://github.com/user-attachments/assets/65fa023d-9b5a-432c-befc-3d27711b6428" />
<img width="1920" height="1080" alt="Screenshot 2026-09-30 190630" src="https://github.com/user-attachments/assets/350b5a83-9a86-4da6-bec1-a430fdd19e20" />


Simulated GPU workload management, task grouping and initial allocation.
No NVIDIA hardware, database or Node.js required.

## Run
    cd backend
    pip install -r requirements.txt
    python app.py
Open http://127.0.0.1:5000

## Algorithm (summary)
1. Workload: load tasks (WAITING) + 3 simulated GPUs (8 units each)
2. Grouping: First-Fit Decreasing bin packing, group limit = partition size (4)
3. Analysis: group requirement vs available GPU capacity -> fits / remaining
4. Partitioning: each GPU split into Partition A (4) + Partition B (4)
5. Wastage: dry-run allocation; Wastage % = unused / total x 100
6. Allocation: Best-Fit partition (least leftover), no over-allocation; tasks -> RUNNING
