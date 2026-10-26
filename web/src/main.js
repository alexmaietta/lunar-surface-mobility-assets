import * as THREE from "three";
import GUI from "three/addons/libs/lil-gui.module.min.js";
import { Viewer } from "./viewer.js";

const BASE = "models";
const REPO = "https://github.com/alexmaietta/lunar-surface-mobility-assets";
const PASSIVE = new Set(["landing_gear", "suspension", "linkage"]);
const ROLE_ORDER = ["gimbal", "steer", "drive", "active_suspension", "antenna", "camera", "arm", "crane", "hatch", "latch", "stair", "railing", "solar", "deploy"];
const ROLE_NAMES = {
  gimbal: "Engine gimbal", steer: "Steering", drive: "Wheels", active_suspension: "Active suspension", antenna: "Antennas",
  camera: "Cameras", arm: "Robotic arm", crane: "Crane", hatch: "Hatches", latch: "Latches", stair: "Stairs",
  railing: "Railings", solar: "Solar arrays", deploy: "Deployables", actuated: "Other",
};
const OVERVIEW = "(overview)";

const $ = (id) => document.getElementById(id);
const viewer = new Viewer($("view"));
const state = { manifest: null, selected: null, animate: false, wheelSpeed: 0, t: 0, controls: [], wheelAngles: new Map() };
const ui = { vehicle: OVERVIEW, progress: "", grid: false, human: true, shadows: true };
let gui, vehicleCtl, progressCtl, loadAllCtl, specs, attach, moving;
let loadingAll = false;

async function loadAll() {
  if (loadingAll) return;
  loadingAll = true;
  loadAllCtl.disable();
  const queue = hosts().filter((a) => !viewer.items.get(a.id).full).sort((a, b) => a.files.full_bytes - b.files.full_bytes);
  const total = queue.reduce((t, a) => t + a.files.full_bytes, 0);
  let done = 0;
  while (queue.length) {
    const i = queue.findIndex((a) => a.id === state.selected);
    const a = queue.splice(i >= 0 ? i : 0, 1)[0];
    loadAllCtl.name(`Detailed models ${fmt.mb(done)} / ${fmt.mb(total)}`);
    await viewer.loadFull(a.id, BASE);
    done += a.files.full_bytes;
  }
  loadAllCtl.name(`All detailed models loaded (${fmt.mb(total)})`);
}

const fmt = {
  m: (v) => `${v.toFixed(v < 10 ? 2 : 1)} m`,
  kg: (v) => (v >= 1000 ? `${(v / 1000).toFixed(v >= 10000 ? 1 : 2)} t` : `${Math.round(v)} kg`),
  kn: (n) => (n >= 1000 ? `${(n / 1000).toFixed(1)} kN` : `${Math.round(n)} N`),
  mb: (b) => `${(b / 1e6).toFixed(1)} MB`,
  label: (s) => s.replace(/_/g, " "),
};

const hosts = () => state.manifest.assets.filter((a) => a.kind !== "attachment");
const byId = (id) => state.manifest.assets.find((x) => x.id === id);

function info(folder, name, value) {
  const o = { v: value };
  return folder.add(o, "v").name(name).disable();
}

function overview(instant = false) {
  if (state.selected) resetPose(byId(state.selected));
  state.selected = null;
  ui.vehicle = OVERVIEW;
  vehicleCtl.updateDisplay();
  for (const f of [specs, attach, moving]) f && f.destroy();
  specs = attach = moving = null;
  viewer.select(null);
  history.replaceState(null, "", location.pathname + location.search);
  viewer.view(viewer.allBounds(), { azimuth: 25, elevation: 10, pad: 0.9, instant });
}

function jointRange(j) {
  if (j.limit) return j.limit;
  return j.type === "revolute" ? [-Math.PI, Math.PI] : null;
}

function resetPose(a) {
  if (!a) return;
  state.animate = false;
  state.wheelSpeed = 0;
  state.wheelAngles.clear();
  for (const j of a.joints) viewer.setJoint(a.id, j, 0);
  for (const c of state.controls) {
    c.params.v = c.zero;
    c.ctl.updateDisplay();
  }
}

function buildSpecs(a) {
  specs = gui.addFolder("Specs");
  info(specs, "Kind", `${a.kind} · ${a.path}`);
  info(specs, "Height", fmt.m(a.dims.height));
  info(specs, "Footprint", `${fmt.m(a.dims.length)} × ${fmt.m(a.dims.width)}`);
  for (const [k, v] of Object.entries(a.mass || {})) info(specs, `Mass, ${fmt.label(k)}${k === a.mass_default ? " *" : ""}`, fmt.kg(v));
  const p = a.propulsion;
  if (p && p.main.length) {
    const t = p.main[0];
    info(specs, "Main engines", `${p.main.length} × ${fmt.kn(t.thrust_n)}, Isp ${Math.round(t.isp_s)} s, ${t.propellant}`);
  }
  if (p) for (const [k, n] of Object.entries(p.other)) info(specs, fmt.label(k), `${n} thrusters`);
  info(specs, "Joints", `${a.joints.length} (${a.joints.filter((j) => !PASSIVE.has(j.role)).length} controllable)`);
  info(specs, "Detailed model", fmt.mb(a.files.full_bytes));
  info(specs, "About", a.doc).domElement.title = a.doc;
  specs.add({ open: () => window.open(`${REPO}/tree/main/assets/${a.path}`, "_blank", "noopener") }, "open").name("Source files ↗");
  specs.add({ open: () => window.open(`${REPO}/releases/latest`, "_blank", "noopener") }, "open").name("Download USD / glTF / OBJ ↗");
}

function buildAttachments(a) {
  if (!a.attachments || !a.attachments.length) return;
  attach = gui.addFolder("Attachments");
  for (const att of a.attachments) {
    const o = { on: false };
    attach.add(o, "on").name(`${att.set}: ${fmt.label(att.option)}`).onChange((v) => viewer.attach(a.id, att, BASE, v));
  }
}

function buildMoving(a) {
  const groups = {};
  for (const j of a.joints) {
    if (PASSIVE.has(j.role) || (j.drive !== "velocity" && !jointRange(j))) continue;
    (groups[j.role] = groups[j.role] || []).push(j);
  }
  const rank = (r) => (ROLE_ORDER.includes(r) ? ROLE_ORDER.indexOf(r) : 99);
  const roles = Object.keys(groups).sort((x, y) => rank(x) - rank(y));
  if (!roles.length) return;
  moving = gui.addFolder("Moving parts");
  moving.add(state, "animate").name("Animate").listen();
  moving.add({ reset: () => resetPose(a) }, "reset").name("Reset pose");
  state.controls = [];
  for (const role of roles) {
    const f = moving.addFolder(`${ROLE_NAMES[role] || fmt.label(role)} (${groups[role].length})`);
    if (groups[role].every((j) => j.drive === "velocity")) {
      f.add(state, "wheelSpeed", -6, 6, 0.1).name("Spin (rad/s)").listen();
      continue;
    }
    for (const j of groups[role]) {
      const [lo, hi] = jointRange(j);
      const deg = j.type === "revolute";
      const k = deg ? 180 / Math.PI : 1000;
      const zero = Math.min(hi, Math.max(lo, 0)) * k;
      const params = { v: zero };
      const ctl = f.add(params, "v", lo * k, hi * k, deg ? 0.5 : 1).name(`${fmt.label(j.name)} (${deg ? "°" : "mm"})`)
        .onChange((v) => viewer.setJoint(a.id, j, v / k));
      state.controls.push({ j, params, ctl, k, zero });
    }
    if (groups[role].length > 6) f.close();
  }
}

async function select(id) {
  const a = byId(id);
  if (!a || a.kind === "attachment") return;
  if (state.selected && state.selected !== id) resetPose(byId(state.selected));
  for (const f of [specs, attach, moving]) f && f.destroy();
  specs = attach = moving = null;
  state.selected = id;
  state.animate = false;
  state.wheelSpeed = 0;
  ui.vehicle = id;
  vehicleCtl.updateDisplay();
  history.replaceState(null, "", `#${id}`);
  buildSpecs(a);
  buildAttachments(a);
  viewer.select(id);
  viewer.view(viewer.boundsOf(id), { azimuth: 35, elevation: 16 });
  if (!viewer.items.get(id).full) {
    progressCtl.show();
    await viewer.loadFull(id, BASE, (loaded, total) => {
      ui.progress = `${fmt.mb(loaded)} / ${fmt.mb(total)}`;
      progressCtl.updateDisplay();
    });
    progressCtl.hide();
  }
  if (state.selected === id) buildMoving(a);
}

function animate(dt) {
  if (!state.selected) return;
  const a = byId(state.selected);
  state.t += dt;
  if (state.wheelSpeed) {
    for (const j of a.joints) {
      if (j.drive !== "velocity") continue;
      const v = (state.wheelAngles.get(j.name) || 0) + state.wheelSpeed * dt;
      state.wheelAngles.set(j.name, v);
      viewer.setJoint(a.id, j, v);
    }
  }
  if (!state.animate) return;
  state.controls.forEach((c, n) => {
    const [lo, hi] = jointRange(c.j);
    const span = Math.min(hi - lo, c.j.type === "revolute" ? Math.PI : 2);
    const mid = Math.min(hi, Math.max(lo, 0)) + (lo + hi > 0 ? span / 2 : lo + hi < 0 ? -span / 2 : 0);
    const v = Math.min(hi, Math.max(lo, mid + (span / 2) * Math.sin(state.t * 0.9 + n * 0.7)));
    c.params.v = v * c.k;
    c.ctl.updateDisplay();
    viewer.setJoint(a.id, c.j, v);
  });
}

function placeHuman() {
  const front = hosts().filter((a) => a.row === 0);
  if (!front.length) return;
  const box = new THREE.Box3();
  for (const a of front) box.expandByObject(viewer.items.get(a.id).group);
  viewer.human.position.set(box.max.x + 1.5, 0, (box.min.z + box.max.z) / 2);
}

function buildGui() {
  gui = new GUI({ title: `Lunar Surface Mobility Assets v${state.manifest.version}`, width: 330 });
  const options = { [OVERVIEW]: OVERVIEW };
  for (const kind of ["lander", "rover"]) {
    for (const a of hosts().filter((x) => x.kind === kind).sort((x, y) => y.dims.height - x.dims.height)) {
      options[`${a.title} (${fmt.m(a.dims.height)})`] = a.id;
    }
  }
  vehicleCtl = gui.add(ui, "vehicle", options).name("Vehicle").onChange((v) => (v === OVERVIEW ? overview() : select(v)));
  gui.add({ overview: () => overview() }, "overview").name("Overview (Esc)");
  progressCtl = gui.add(ui, "progress").name("Loading model").disable();
  progressCtl.hide();
  loadAllCtl = gui.add({ load: () => loadAll() }, "load").name("Load all detailed models");
  const view = gui.addFolder("View");
  view.add(ui, "grid").name("1 m grid").onChange((v) => (viewer.grid.visible = v));
  view.add(ui, "human").name("1.8 m human").onChange((v) => (viewer.human.visible = v));
  view.add(ui, "shadows").name("Shadows").onChange((v) => (viewer.sun.castShadow = v));
  view.close();
}

function wireInput() {
  const canvas = $("view");
  let down = null;
  canvas.addEventListener("pointerdown", (e) => (down = { x: e.clientX, y: e.clientY }));
  canvas.addEventListener("pointerup", (e) => {
    if (down && Math.hypot(e.clientX - down.x, e.clientY - down.y) < 5) {
      const id = viewer.pick(e.clientX, e.clientY);
      if (id) select(id);
    }
    down = null;
  });
  let pending = false;
  canvas.addEventListener("pointermove", (e) => {
    if (pending || e.buttons) return;
    pending = true;
    requestAnimationFrame(() => {
      pending = false;
      const id = viewer.pick(e.clientX, e.clientY);
      const tip = $("tooltip");
      if (id) {
        const a = byId(id);
        tip.textContent = `${a.title} · ${fmt.m(a.dims.height)}`;
        tip.style.left = `${e.clientX + 14}px`;
        tip.style.top = `${e.clientY + 14}px`;
        tip.classList.remove("hidden");
        canvas.style.cursor = "pointer";
      } else {
        tip.classList.add("hidden");
        canvas.style.cursor = "";
      }
    });
  });
  window.addEventListener("keydown", (e) => {
    if (e.key === "Escape") overview();
  });
  window.addEventListener("hashchange", () => {
    const id = location.hash.slice(1);
    if (id && id !== state.selected) select(id);
  });
}

async function main() {
  const res = await fetch(`${BASE}/manifest.json`);
  if (!res.ok) {
    $("loading").querySelector("span").textContent = "No models found: run ./pipeline.sh web first.";
    return;
  }
  state.manifest = await res.json();
  buildGui();
  wireInput();
  viewer.onFrame = animate;
  let done = 0;
  const list = hosts();
  const bar = $("loading").querySelector(".bar > div");
  await Promise.all(list.map((a) => viewer.loadPreview(a, BASE).then(() => {
    bar.style.width = `${(100 * ++done) / list.length}%`;
  })));
  placeHuman();
  $("loading").classList.add("hidden");
  const id = location.hash.slice(1);
  overview(true);
  if (id) select(id);
  if (!new URLSearchParams(location.search).has("lite")) loadAll();
}

main();
