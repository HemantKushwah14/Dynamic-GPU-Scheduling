from flask import Flask, jsonify, request
from simulation import Simulation, DEFAULT_CFG
from task_manager import read_rows

app = Flask(__name__, static_folder="../frontend", static_url_path="")
sim = Simulation()


@app.route("/")
def index():
    return app.send_static_file("index.html")


def state():
    return jsonify(sim.state())


@app.errorhandler(ValueError)
def bad_input(e):
    return jsonify(error=str(e)), 400


# ---- GET ----
@app.get("/api/state")
def get_state(): return state()

@app.get("/api/tasks")
def get_tasks(): return jsonify(sim.state()["tasks"])

@app.get("/api/gpus")
def get_gpus(): return jsonify(sim.state()["gpus"])

@app.get("/api/groups")
def get_groups(): return jsonify(sim.state()["groups"])

@app.get("/api/partitions")
def get_partitions(): return jsonify(sim.state()["partitions"])

@app.get("/api/allocations")
def get_allocations(): return jsonify(sim.state()["allocations"])

@app.get("/api/metrics")
def get_metrics(): return jsonify(sim.state()["metrics"])

@app.get("/api/config")
def get_config(): return jsonify(sim.state()["config"])


# ---- POST ----
@app.post("/api/config")
def set_config():
    d = request.get_json(silent=True) or {}
    if d.get("sample"):                       # restore sample workload + defaults
        sim.configure(read_rows(), DEFAULT_CFG)
    else:
        sim.configure(d.get("tasks"), d)
    return state()

@app.post("/api/load-workload")
def load_workload(): sim.load_workload(); return state()

@app.post("/api/initialize")
def initialize(): sim.initialize_gpus(); return state()

@app.post("/api/run-phase1")
def run_phase1(): sim.run_phase1(); return state()

@app.post("/api/run-phase2")
def run_phase2(): sim.run_phase2(); return state()

@app.post("/api/step")
def step(): sim.step(); return state()

@app.post("/api/pause")
def pause(): sim.paused = True; return state()

@app.post("/api/reset")
def reset(): sim.reset(); return state()


if __name__ == "__main__":
    app.run(debug=True, port=5000)