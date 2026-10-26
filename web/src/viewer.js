import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";

const SUN_AZIMUTH = THREE.MathUtils.degToRad(-35);
const SUN_ELEVATION = THREE.MathUtils.degToRad(22);

function regolithTexture() {
  const n = 512;
  const c = document.createElement("canvas");
  c.width = c.height = n;
  const g = c.getContext("2d");
  const img = g.createImageData(n, n);
  for (let i = 0; i < n * n; i++) {
    const v = 112 + Math.random() * 30 - 15;
    img.data.set([v, v * 0.985, v * 0.955, 255], i * 4);
  }
  g.putImageData(img, 0, 0);
  for (let k = 0; k < 140; k++) {
    const r = 3 + Math.random() ** 3 * 30;
    const x = Math.random() * n, y = Math.random() * n;
    const grad = g.createRadialGradient(x, y, r * 0.2, x, y, r);
    grad.addColorStop(0, "rgba(60,58,55,0.16)");
    grad.addColorStop(0.75, "rgba(80,78,74,0.06)");
    grad.addColorStop(1, "rgba(180,176,170,0.0)");
    g.fillStyle = grad;
    g.beginPath();
    g.arc(x, y, r, 0, Math.PI * 2);
    g.fill();
  }
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.repeat.set(90, 90);
  t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = 8;
  return t;
}

function stars(count = 4000, radius = 900) {
  const p = new Float32Array(count * 3);
  for (let i = 0; i < count; i++) {
    const u = Math.random() * 2 - 1, a = Math.random() * Math.PI * 2;
    const s = Math.sqrt(1 - u * u);
    p.set([radius * s * Math.cos(a), radius * Math.abs(u) + 20, radius * s * Math.sin(a)], i * 3);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.BufferAttribute(p, 3));
  return new THREE.Points(g, new THREE.PointsMaterial({ color: 0xffffff, size: 1.3, sizeAttenuation: false, transparent: true, opacity: 0.8 }));
}

function human() {
  const m = new THREE.MeshStandardMaterial({ color: 0xe8e4dc, roughness: 0.7 });
  const g = new THREE.Group();
  const add = (geo, x, y, z) => {
    const mesh = new THREE.Mesh(geo, m);
    mesh.position.set(x, y, z);
    mesh.castShadow = true;
    g.add(mesh);
  };
  add(new THREE.SphereGeometry(0.12, 24, 16), 0, 1.68, 0);
  add(new THREE.CapsuleGeometry(0.17, 0.48, 6, 16), 0, 1.22, 0);
  add(new THREE.CapsuleGeometry(0.07, 0.62, 6, 12), -0.09, 0.42, 0);
  add(new THREE.CapsuleGeometry(0.07, 0.62, 6, 12), 0.09, 0.42, 0);
  add(new THREE.CapsuleGeometry(0.05, 0.52, 6, 12), -0.25, 1.15, 0);
  add(new THREE.CapsuleGeometry(0.05, 0.52, 6, 12), 0.25, 1.15, 0);
  return g;
}

function prepare(root) {
  root.traverse((o) => {
    if (o.isMesh) {
      o.castShadow = true;
      o.receiveShadow = true;
      const mats = Array.isArray(o.material) ? o.material : [o.material];
      for (const m of mats) if (m && m.map) m.map.anisotropy = 8;
    }
  });
}

export class Viewer {
  constructor(canvas) {
    this.canvas = canvas;
    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true, logarithmicDepthBuffer: true });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.1;
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;

    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x000000);
    const pmrem = new THREE.PMREMGenerator(this.renderer);
    this.scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
    this.scene.environmentIntensity = 0.35;
    this.scene.add(stars());

    this.camera = new THREE.PerspectiveCamera(35, 1, 0.1, 3000);
    this.controls = new OrbitControls(this.camera, canvas);
    this.controls.enableDamping = true;
    this.controls.maxPolarAngle = THREE.MathUtils.degToRad(88);
    this.controls.minDistance = 0.5;
    this.controls.maxDistance = 400;

    this.sun = new THREE.DirectionalLight(0xfff6ea, 4.2);
    this.sun.castShadow = true;
    this.sun.shadow.mapSize.set(4096, 4096);
    this.sun.shadow.bias = -0.0004;
    this.sun.shadow.normalBias = 0.03;
    this.scene.add(this.sun, this.sun.target);
    this.scene.add(new THREE.HemisphereLight(0x9aa4b4, 0x3a3836, 0.35));

    const ground = new THREE.Mesh(new THREE.PlaneGeometry(1200, 1200),
      new THREE.MeshStandardMaterial({ map: regolithTexture(), roughness: 1, metalness: 0 }));
    ground.rotation.x = -Math.PI / 2;
    ground.receiveShadow = true;
    this.scene.add(ground);
    this.grid = new THREE.GridHelper(120, 120, 0x8a8a8a, 0x5a5a5a);
    this.grid.position.y = 0.002;
    this.grid.material.transparent = true;
    this.grid.material.opacity = 0.35;
    this.grid.visible = false;
    this.scene.add(this.grid);
    this.human = human();
    this.scene.add(this.human);
    this.ring = new THREE.Mesh(new THREE.RingGeometry(0.96, 1, 96), new THREE.MeshBasicMaterial({ color: 0x6fb6ff, transparent: true, opacity: 0.8 }));
    this.ring.rotation.x = -Math.PI / 2;
    this.ring.position.y = 0.01;
    this.ring.visible = false;
    this.scene.add(this.ring);

    this.loader = new GLTFLoader();
    this.items = new Map();
    this.raycaster = new THREE.Raycaster();
    this.clock = new THREE.Clock();
    this.fly = null;
    this.onFrame = null;
    window.addEventListener("resize", () => this.resize());
    this.resize();
    this.renderer.setAnimationLoop(() => this.frame());
  }

  resize() {
    const w = window.innerWidth, h = window.innerHeight;
    this.renderer.setSize(w, h, false);
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
  }

  async loadPreview(entry, base) {
    const file = entry.files.preview || entry.files.full;
    const gltf = await this.loader.loadAsync(`${base}/${file}`);
    const group = new THREE.Group();
    group.position.fromArray(entry.position || [0, 0, 0]);
    group.userData.assetId = entry.id;
    prepare(gltf.scene);
    group.add(gltf.scene);
    this.scene.add(group);
    this.items.set(entry.id, { entry, group, preview: gltf.scene, full: null, nodes: new Map(), rest: new Map(), attached: new Map() });
    return group;
  }

  loadFull(id, base, onProgress) {
    const it = this.items.get(id);
    if (it.full) return Promise.resolve(it);
    if (!it.loading) {
      it.listeners = [];
      it.loading = this._loadFull(it, base).finally(() => (it.loading = null));
    }
    if (onProgress) it.listeners.push(onProgress);
    return it.loading;
  }

  async _loadFull(it, base) {
    const total = it.entry.files.full_bytes;
    const gltf = await this.loader.loadAsync(`${base}/${it.entry.files.full}`, (e) => {
      for (const f of it.listeners) f(e.loaded, e.total || total);
    });
    prepare(gltf.scene);
    it.full = gltf.scene;
    it.group.add(gltf.scene);
    it.preview.visible = false;
    gltf.scene.traverse((o) => {
      if (o.name && !it.nodes.has(o.name)) {
        it.nodes.set(o.name, o);
        it.rest.set(o.name, { p: o.position.clone(), q: o.quaternion.clone() });
      }
    });
    return it;
  }

  async attach(id, att, base, on) {
    const host = this.items.get(id);
    let a = host.attached.get(att.asset);
    if (!a && on) {
      const gltf = await this.loader.loadAsync(`${base}/${att.asset}/full.glb`);
      prepare(gltf.scene);
      gltf.scene.position.fromArray(att.position);
      host.group.add(gltf.scene);
      a = gltf.scene;
      host.attached.set(att.asset, a);
    }
    if (a) a.visible = on;
    return a;
  }

  setJoint(id, joint, value) {
    const it = this.items.get(id);
    const node = it && it.nodes.get(joint.node);
    if (!node) return;
    const rest = it.rest.get(joint.node);
    const axis = new THREE.Vector3().fromArray(joint.axis).normalize();
    if (joint.type === "revolute") {
      node.quaternion.copy(rest.q).multiply(new THREE.Quaternion().setFromAxisAngle(axis, value));
    } else {
      node.position.copy(rest.p).addScaledVector(axis, value);
    }
  }

  boundsOf(id) {
    const it = this.items.get(id);
    return new THREE.Box3().setFromObject(it.group);
  }

  allBounds() {
    const b = new THREE.Box3();
    for (const it of this.items.values()) b.expandByObject(it.group);
    return b;
  }

  fitShadow(box) {
    const c = box.getCenter(new THREE.Vector3());
    const r = Math.max(4, box.getSize(new THREE.Vector3()).length() * 0.6);
    const d = new THREE.Vector3(Math.cos(SUN_ELEVATION) * Math.sin(SUN_AZIMUTH), Math.sin(SUN_ELEVATION), Math.cos(SUN_ELEVATION) * Math.cos(SUN_AZIMUTH));
    this.sun.position.copy(c).addScaledVector(d, r * 3);
    this.sun.target.position.copy(c);
    const cam = this.sun.shadow.camera;
    cam.left = cam.bottom = -r;
    cam.right = cam.top = r;
    cam.near = 0.1;
    cam.far = r * 6;
    cam.updateProjectionMatrix();
  }

  view(box, { azimuth = 25, elevation = 14, pad = 1.15, instant = false } = {}) {
    const size = box.getSize(new THREE.Vector3());
    const c = box.getCenter(new THREE.Vector3());
    const fov = THREE.MathUtils.degToRad(this.camera.fov);
    const fitH = (size.y * pad) / 2 / Math.tan(fov / 2);
    const fitW = (Math.max(size.x, size.z) * pad) / 2 / Math.tan(fov / 2) / this.camera.aspect;
    const dist = Math.max(fitH, fitW, 2) + Math.max(size.x, size.z) * 0.25;
    const az = THREE.MathUtils.degToRad(azimuth), el = THREE.MathUtils.degToRad(elevation);
    const target = new THREE.Vector3(c.x, Math.max(c.y * 0.8, 0.3), c.z);
    const pos = target.clone().add(new THREE.Vector3(Math.sin(az) * Math.cos(el), Math.sin(el), Math.cos(az) * Math.cos(el)).multiplyScalar(dist));
    this.fitShadow(box);
    if (instant) {
      this.camera.position.copy(pos);
      this.controls.target.copy(target);
      return;
    }
    this.fly = { t: 0, p0: this.camera.position.clone(), p1: pos, t0: this.controls.target.clone(), t1: target };
  }

  select(id) {
    if (!id) {
      this.ring.visible = false;
      return;
    }
    const box = this.boundsOf(id);
    const size = box.getSize(new THREE.Vector3());
    const c = box.getCenter(new THREE.Vector3());
    const r = Math.max(size.x, size.z) * 0.62;
    this.ring.position.set(c.x, 0.01, c.z);
    this.ring.scale.setScalar(r);
    this.ring.visible = true;
  }

  pick(clientX, clientY) {
    const rect = this.canvas.getBoundingClientRect();
    const v = new THREE.Vector2(((clientX - rect.left) / rect.width) * 2 - 1, -((clientY - rect.top) / rect.height) * 2 + 1);
    this.raycaster.setFromCamera(v, this.camera);
    const groups = [...this.items.values()].map((it) => it.group);
    const hit = this.raycaster.intersectObjects(groups, true).find((h) => h.object.visible);
    if (!hit) return null;
    let o = hit.object;
    while (o && !o.userData.assetId) o = o.parent;
    return o ? o.userData.assetId : null;
  }

  frame() {
    const dt = Math.min(this.clock.getDelta(), 0.1);
    if (this.fly) {
      this.fly.t = Math.min(1, this.fly.t + dt / 1.1);
      const k = this.fly.t < 0.5 ? 4 * this.fly.t ** 3 : 1 - (-2 * this.fly.t + 2) ** 3 / 2;
      this.camera.position.lerpVectors(this.fly.p0, this.fly.p1, k);
      this.controls.target.lerpVectors(this.fly.t0, this.fly.t1, k);
      if (this.fly.t >= 1) this.fly = null;
    }
    if (this.onFrame) this.onFrame(dt);
    this.controls.update();
    this.renderer.render(this.scene, this.camera);
  }
}
