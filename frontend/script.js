const BASE_DELAY = 1600;                 // ms between stages at 1x
const PAL = ["#4F86C6", "#3C6E71", "#F4A261", "#E76F51", "#8E6FD1", "#2BB3A3", "#D9558B", "#7A9E3B"];
const gcol = id => PAL[(parseInt(String(id).slice(1)) - 1) % PAL.length];
let S = null, speed = 1, running = false, timer = null;
let draft = { rows: [], gpu_count: 3, capacity: 8, partition_size: 4 };
const $ = id => document.getElementById(id);

// ---------- helpers ----------
function toast(msg, good) {
  const t = $("toast"); t.textContent = msg; t.className = "show" + (good ? " good" : "");
  clearTimeout(toast.h); toast.h = setTimeout(() => t.className = "", 3500);
}
async function api(path, method = "POST", body) {
  try {
    const r = await fetch("/api/" + path, {
      method, headers: { "Content-Type": "application/json" },
      body: body ? JSON.stringify(body) : undefined
    });
    const d = await r.json();
    if (!r.ok) throw new Error(d.error || "Request failed");
    return d;
  } catch (e) { toast("⚠ " + e.message); return null; }
}
async function act(path, body) {
  const d = await api(path, "POST", body);
  if (d) { S = d; render(); }
  return d;
}

// ---------- run / pause / step ----------
function stop() { running = false; clearTimeout(timer); $("btnRun").textContent = "▶ Run"; $("btnRun").classList.remove("on"); }
async function tick() {
  if (!running) return;
  const d = await act("step");
  if (!d || S.stage >= 6) return stop();
  timer = setTimeout(tick, BASE_DELAY / speed);      // delay depends on speed
}
function run() {
  if (running || (S && S.stage >= 6)) return;
  running = true; $("btnRun").textContent = "Running…"; $("btnRun").classList.add("on"); tick();
}
$("btnLoad").onclick = () => { stop(); act("load-workload"); };
$("btnInit").onclick = () => { stop(); act("initialize"); };
$("btnRun").onclick = run;
$("btnPause").onclick = async () => { stop(); await act("pause"); };
$("btnStep").onclick = () => { stop(); act("step"); };      // exactly ONE stage
$("btnReset").onclick = () => { stop(); act("reset"); };

document.querySelectorAll(".spd").forEach(b => b.onclick = () => {
  speed = parseFloat(b.dataset.s);
  document.querySelectorAll(".spd").forEach(x => x.classList.toggle("active", x === b));
  if (running) { clearTimeout(timer); timer = setTimeout(tick, BASE_DELAY / speed); }
});

// ---------- settings editor (values changed on the website) ----------
function loadDraft(c) {
  draft = { rows: c.rows.map(r => ({ ...r })), gpu_count: c.gpu_count, capacity: c.capacity, partition_size: c.partition_size };
  renderEditor();
}
function renderEditor() {
  $("cfg").innerHTML = `
    <div class="cfgrow">
      <label>Number of GPUs (1-6)<input type="number" value="${draft.gpu_count}" oninput="draft.gpu_count=this.value"></label>
      <label>Capacity per GPU (2-32)<input type="number" value="${draft.capacity}" oninput="draft.capacity=this.value"></label>
      <label>Partition size<input type="number" value="${draft.partition_size}" oninput="draft.partition_size=this.value"></label>
    </div>
    <div class="tedit"><table><tr><th>Task</th><th>GPU Required</th><th>Arrival Time</th><th>Execution Time</th><th></th></tr>
      ${draft.rows.map((r, i) => `<tr><td><b>T${i + 1}</b></td>
        <td><input type="number" value="${r.gpu}" oninput="draft.rows[${i}].gpu=this.value"></td>
        <td><input type="number" value="${r.arrival}" oninput="draft.rows[${i}].arrival=this.value"></td>
        <td><input type="number" value="${r.exec_time}" oninput="draft.rows[${i}].exec_time=this.value"></td>
        <td><button class="del" onclick="delRow(${i})">✕</button></td></tr>`).join("")}
    </table></div>
    <button onclick="addRow()">➕ Add Task</button>
    <button class="ok" onclick="applyCfg()">✔ Apply &amp; Load</button>
    <button onclick="useSample()">Sample Data</button>`;
}
function addRow() { draft.rows.push({ gpu: 1, arrival: 0, exec_time: 10 }); renderEditor(); }
function delRow(i) { draft.rows.splice(i, 1); renderEditor(); }
async function applyCfg() {
  stop();
  const d = await act("config", { tasks: draft.rows, gpu_count: draft.gpu_count, capacity: draft.capacity, partition_size: draft.partition_size });
  if (d) { loadDraft(S.config); toast("Settings applied. Press Step or Run.", true); }
}
async function useSample() {
  stop();
  const d = await act("config", { sample: true });
  if (d) { loadDraft(S.config); toast("Sample data restored.", true); }
}

// ---------- rendering ----------
const badge = (s, cls) => `<span class="badge ${cls || s}">${s}</span>`;
const bar = p => `<div class="bar"><i data-w="${p}" class="${p > 90 ? "hi" : ""}"></i></div>`;
const table = (head, rows) => rows.length
  ? `<table><tr>${head.map(h => `<th>${h}</th>`).join("")}</tr>${rows.map(r => `<tr class="pop">${r.map(c => `<td>${c}</td>`).join("")}</tr>`).join("")}</table>`
  : `<p class="muted">No data yet.</p>`;

function animate(el, to, suffix = "") {          // counting animation
  if (typeof to === "string") { el.textContent = to; el.dataset.v = 0; return; }
  const from = parseFloat(el.dataset.v) || 0, t0 = performance.now(); el.dataset.v = to;
  (function f(t) {
    const p = Math.min(1, (t - t0) / 600);
    el.textContent = (p < 1 ? Math.round(from + (to - from) * p) : to) + suffix;
    if (p < 1) requestAnimationFrame(f);
  })(t0);
}

const STATS = [["Total GPUs", "#4F86C6"], ["Available GPUs", "#2BB3A3"], ["Waiting Tasks", "#F4A261"],
  ["Running Tasks", "#4F86C6"], ["Completed Tasks", "#4CAF50"], ["GPU Utilization", "#8E6FD1"], ["Resource Wastage", "#E76F51"]];

function render() {
  const m = S.metrics, tg = {};
  S.tasks.forEach(t => tg[t.id] = t.group);
  const chip = id => `<span class="chip" style="${tg[id] ? "background:" + gcol(tg[id]) : ""}">${id}</span>`;

  // summary cards (built once, then values animate)
  if (!$("cards").children.length)
    $("cards").innerHTML = STATS.map(([l, c], i) => `<div class="stat" style="--c:${c};animation-delay:${i * 60}ms"><b>0</b><span>${l}</span></div>`).join("");
  const vals = [[m.total_gpus], [m.available_gpus], [m.waiting], [m.running], [m.completed],
    [m.utilization, "%"], [m.wastage ? m.wastage.overall : "—", "%"]];
  [...$("cards").children].forEach((c, i) => animate(c.querySelector("b"), vals[i][0], vals[i][1] || ""));

  $("prog").firstElementChild.style.width = (S.stage / 6 * 100) + "%";

  $("flow").innerHTML = `<div class="flow">${S.stages.map((n, i) =>
    `<div class="stage ${i + 1 === S.stage ? "active" : i + 1 < S.stage ? "done" : ""}">${i + 1}. ${n.toUpperCase()}</div>`).join("")}</div>`;
  $("explainBody").innerHTML = `<div class="explain-title">${S.stage_name}</div><p>${S.explanation}</p>` +
    (S.stage === 0 ? `<p class="muted">Press Step or Run to begin (workload and GPUs load automatically).</p>` : "");

  $("tasks").innerHTML = table(["Task", "Arrival", "GPU Req", "Exec", "Group", "Status"],
    S.tasks.map(t => [`<b>${t.id}</b>`, t.arrival, t.gpu, t.exec_time, t.group ? chip(t.group).replace(/>G/, ">G") : "-", badge(t.status)]));

  $("gpus").innerHTML = S.gpus.length ? S.gpus.map(g => `
    <div class="gpu" style="border-left-color:${PAL[(g.id - 1) % PAL.length]}"><b>🖥️ GPU ${g.id}</b>
      <small>Total: ${g.capacity} | Used: ${g.used} | Available: ${g.available} | Wastage: ${g.wastage}%</small>
      ${bar(g.utilization)}<small>Utilization ${g.utilization}%</small>
      ${g.partitions.map(p => `<small>Partition ${p.label}: ${p.used}/${p.capacity} — ${p.tasks.map(chip).join("") || "empty"}</small>`).join("")}
    </div>`).join("") : `<p class="muted">GPUs not initialized.</p>`;

  $("groups").innerHTML = S.groups.length ? S.groups.map(g => `
    <div class="grp" style="--c:${gcol(g.id)}"><b>${g.id.replace("G", "GROUP ")}</b><br>${g.tasks.map(chip).join("")}<br>
      Total: ${g.total} units<br>${badge("Compatible", "yes")}</div>`).join("")
    : `<p class="muted">Groups appear after Task Grouping.</p>`;

  $("analysis").innerHTML = table(["Group", "Tasks", "Required", "Available", "Fits", "Remaining"],
    S.analysis.map(a => [a.group, a.num_tasks, a.required, a.available, badge(a.fits ? "Yes" : "No", a.fits ? "yes" : "no"), a.remaining]));

  $("parts").innerHTML = S.gpus.some(g => g.partitions.length) ? S.gpus.map(g => `
    <b>🖥️ GPU ${g.id}</b>${g.partitions.map(p => `
      <div class="pbox" style="--c:${p.groups.length ? gcol(p.groups[0]) : "#3C6E71"}">
        <b>Partition ${p.label}</b> — Capacity: ${p.capacity}, Used: ${p.used}, Free: ${p.available}
        ${bar(p.used / p.capacity * 100)}${p.tasks.map(chip).join("") || "<span class='muted'>unallocated</span>"}</div>`).join("")}`).join("")
    : `<p class="muted">Partitions appear after GPU Partitioning.</p>`;

  $("alloc").innerHTML = table(["Group", "GPU", "Partition", "Required", "Unused", "Status"],
    S.allocations.map(a => [a.group, a.gpu, a.partition, a.required, a.unused, badge(a.status, a.status.startsWith("Alloc") ? "Allocated" : "Waiting")]));

  const max = Math.max(1, ...S.tasks.map(t => t.arrival));
  $("timeline").innerHTML = S.tasks.length
    ? `<div class="line">${S.tasks.map((t, i) => `<div class="mk" style="left:${t.arrival / max * 100}%;--c:${tg[t.id] ? gcol(tg[t.id]) : "#3C6E71"};animation-delay:${i * 60}ms"><i></i>${t.id}<br>${t.arrival}s</div>`).join("")}</div>`
    : `<p class="muted">Load the workload to see arrivals.</p>`;

  requestAnimationFrame(() => requestAnimationFrame(() =>       // animate bar fill
    document.querySelectorAll(".bar i[data-w]").forEach(i => i.style.width = i.dataset.w + "%")));
}

api("state", "GET").then(s => { if (s) { S = s; loadDraft(S.config); render(); } });