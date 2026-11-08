import math
import os
import sys

import numpy as np
import warp as wp

import newton
import newton.examples
from example_robot_rover import find_usd, usd_roles
from newton.solvers import SolverImplicitMPM

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(REPO, "scripts"))
import assetcfg

G_MOON = 1.625
CFG = assetcfg.load("ipex")
SHOULDER_X, SHOULDER_Z = CFG.SHOULDER
ARM_LEN, ARM_POSE = CFG.ARM_LEN, CFG.ARM_POSE
DRUM_R, DRUM_Y = CFG.DRUM_R, CFG.DRUM_Y
WHEEL_R = CFG.R_W - CFG.GROUSER_H / 2
WHEELS = ("fl_wheel", "fr_wheel", "rl_wheel", "rr_wheel")
REC_LO, REC_HI = np.array([-1.0, -1.0, -0.2]), np.array([3.0, 1.0, 1.0])


@wp.kernel
def _impulse_wrench(impulse: wp.array(dtype=wp.vec3), pos: wp.array(dtype=wp.vec3), cid: wp.array(dtype=int),
                    collider_body: wp.array(dtype=int), body_q: wp.array(dtype=wp.transform), body_com: wp.array(dtype=wp.vec3),
                    inv_dt: float, out: wp.array(dtype=wp.spatial_vector)):
    i = wp.tid()
    c = cid[i]
    if c < 0:
        return
    b = collider_body[c]
    if b < 0:
        return
    f = impulse[i] * inv_dt
    com = wp.transform_point(body_q[b], body_com[b])
    wp.atomic_add(out, b, wp.spatial_vector(f, wp.cross(pos[i] - com, f)))


@wp.kernel
def _add_wrench(src: wp.array(dtype=wp.spatial_vector), dst: wp.array(dtype=wp.spatial_vector)):
    i = wp.tid()
    dst[i] = dst[i] + src[i]


def arm_angle_for(drum_bottom_z, ride_z):
    zc = drum_bottom_z + DRUM_R - ride_z
    return math.asin(max(-1.0, min(1.0, (zc - SHOULDER_Z) / ARM_LEN))) - ARM_POSE


def smoothstep(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


class Example:
    def __init__(self, viewer, args):
        self.viewer, self.args = viewer, args
        self.fps = 60
        self.frame_dt = 1.0 / self.fps
        self.sim_substeps = args.substeps
        self.sim_dt = self.frame_dt / self.sim_substeps
        self.sim_time = 0.0
        self.frame = 0
        g = 9.81 if args.earth else G_MOON

        from pxr import Usd

        stage = Usd.Stage.Open(args.usd or find_usd("ipex"))
        root = stage.GetDefaultPrim()
        for kv in [x for x in (args.variants or "").split(",") if x]:
            k, v = kv.split("=")
            root.GetVariantSet(k).SetVariantSelection(v)
        root.GetVariantSet("Physics").SetVariantSelection("physics")
        roles = usd_roles(stage)

        newton.use_coord_layout_targets = True
        builder = newton.ModelBuilder(up_axis=newton.Axis.Z, gravity=(0.0, 0.0, -g))
        newton.solvers.SolverMuJoCo.register_custom_attributes(builder)
        SolverImplicitMPM.register_custom_attributes(builder)
        builder.default_shape_cfg.mu = 0.8
        builder.default_shape_cfg.ke = 2.0e5
        builder.default_shape_cfg.kd = 5.0e3
        builder.add_usd(stage, xform=wp.transform(wp.vec3(0.0, 0.0, 0.02), wp.quat_identity()), collapse_fixed_joints=False,
                        enable_self_collisions=False, hide_collision_shapes=True)
        self.labels = [s.rsplit("/", 1)[-1] for s in builder.joint_label]
        self.blabels = [s.rsplit("/", 1)[-1] for s in builder.body_label]
        self.coord = {n: builder.joint_q_start[i] for i, n in enumerate(self.labels)}
        self.dof = {n: builder.joint_qd_start[i] for i, n in enumerate(self.labels)}
        self.role = {n: roles.get(n, "") for n in self.labels}
        diggers = {"front_drums", "rear_drums", *WHEELS}
        for b in range(builder.body_count):
            for s in builder.body_shapes[b]:
                if self.blabels[b] not in diggers:
                    builder.shape_flags[s] = builder.shape_flags[s] & ~newton.ShapeFlags.COLLIDE_PARTICLES
                elif builder.shape_type[s] == newton.GeoType.CONVEX_MESH:
                    builder.shape_type[s] = newton.GeoType.MESH
        builder.add_ground_plane(color=(0.42, 0.41, 0.39))

        self.bed_lo = np.array([args.bed_start, -args.bed_half_width, 0.0])
        self.bed_hi = np.array([args.bed_start + args.bed_length, args.bed_half_width, args.bed_depth])
        res = np.array(np.ceil(args.particles_per_cell * (self.bed_hi - self.bed_lo) / args.voxel_size), dtype=int)
        cell = (self.bed_hi - self.bed_lo) / res
        radius = float(np.max(cell) * 0.5)
        self.particle_mass = float(np.prod(cell) * args.density)
        builder.add_particle_grid(pos=wp.vec3(self.bed_lo), rot=wp.quat_identity(), vel=wp.vec3(0.0), dim_x=res[0] + 1, dim_y=res[1] + 1,
                                  dim_z=res[2] + 1, cell_x=cell[0], cell_y=cell[1], cell_z=cell[2], mass=self.particle_mass,
                                  jitter=2.0 * radius, radius_mean=radius,
                                  custom_attributes={"mpm:friction": math.tan(math.radians(args.friction_angle)),
                                                     "mpm:yield_stress": args.cohesion, "mpm:dilatancy": args.dilatancy,
                                                     "mpm:young_modulus": args.young_modulus, "mpm:poisson_ratio": args.poisson})
        self.model = builder.finalize()
        self.bed_mass = self.particle_mass * self.model.particle_count

        self.solver = newton.solvers.SolverMuJoCo(self.model, iterations=100, ls_iterations=50, cone="elliptic", impratio=10, njmax=1200,
                                                  nconmax=512)
        mpm = SolverImplicitMPM.Config()
        mpm.voxel_size = args.voxel_size
        mpm.tolerance = 1.0e-6
        mpm.transfer_scheme = "pic"
        mpm.grid_type = "sparse"
        mpm.strain_basis = "P0"
        mpm.max_iterations = 50
        mpm.critical_fraction = 0.0
        mpm.air_drag = 1.0
        mpm.collider_velocity_mode = "backward"
        self.mpm = SolverImplicitMPM(self.model, config=mpm)

        self.state_0, self.state_1 = self.model.state(), self.model.state()
        self.control = self.model.control()
        newton.eval_fk(self.model, self.model.joint_q, self.model.joint_qd, self.state_0)
        self.mpm.setup_collider(body_mass=self.model.body_mass if args.two_way else wp.zeros_like(self.model.body_mass),
                                body_q=self.state_0.body_q)
        self.mpm_wrench = wp.zeros(self.model.body_count, dtype=wp.spatial_vector)
        self.pipe = newton.CollisionPipeline(self.model, soft_contact_max=0)
        self.contacts = self.pipe.contacts()
        self.tq = self.control.joint_target_q.numpy()
        self.tqd = self.control.joint_target_qd.numpy()
        self.home = {n: float(self.tq[self.coord[n]]) for n in ("front_arm", "rear_arm", "radiator_cover")}
        self.dig_q = arm_angle_for(args.bed_depth - args.dig_depth, 0.004)
        self.carry_q = math.radians(args.carry_deg)
        phases = [("carry", 1.0), ("lower", 2.0), ("dig", args.dig_time)]
        if args.fill_revs > 0:
            phases.append(("fill", args.fill_revs * 2 * math.pi / args.drum_speed))
        phases.append(("lift", 2.5))
        if args.transit > 0:
            phases.append(("transit", args.transit / args.transit_speed + 1.0))
        phases += [("weigh", 1.5), ("dump", args.dump_time), ("done", 0.0)]
        self.plan, t0 = [], 0.0
        for name, dur in phases:
            self.plan.append((t0, name, dur))
            t0 += dur
        self.duration = t0
        self.phase = "carry"
        self.collected = {}
        self.front = self.blabels.index("front_drums")
        self.record = {"body_q": [], "particle_q": [], "t": [], "phase": []} if args.record else None
        self.viewer.set_model(self.model)
        self.viewer.show_particles = True
        print(f"ipex dig: {self.model.particle_count} particles, {self.bed_mass:.1f} kg regolith bed, voxel {args.voxel_size * 1000:.0f} mm, "
              f"dig depth {args.dig_depth * 100:.1f} cm (front arm {math.degrees(self.dig_q):+.1f} deg), "
              f"{'two-way' if args.two_way else 'one-way'} coupling, friction angle {args.friction_angle:.0f} deg, cohesion {args.cohesion:.0f} Pa, "
              f"sequence {self.duration:.1f} s ({math.ceil(self.duration * self.fps) + 30} frames)")
        self.capture()

    def capture(self):
        self.graph = None
        if wp.get_device().is_cuda:
            with wp.ScopedCapture() as capture:
                self.simulate_rover()
            self.graph = capture.graph

    def simulate_rover(self):
        self.pipe.collide(self.state_0, self.contacts)
        for _ in range(self.sim_substeps):
            self.state_0.clear_forces()
            wp.launch(_add_wrench, dim=self.model.body_count, inputs=[self.mpm_wrench, self.state_0.body_f])
            self.solver.step(self.state_0, self.state_1, self.control, self.contacts, self.sim_dt)
            self.state_0, self.state_1 = self.state_1, self.state_0

    def simulate_regolith(self):
        self.mpm.step(self.state_0, self.state_0, contacts=None, control=None, dt=self.frame_dt)
        if self.args.two_way:
            self.mpm_wrench.zero_()
            imp, pos, cid = self.mpm.collect_collider_impulses(self.state_0)
            wp.launch(_impulse_wrench, dim=imp.shape[0], inputs=[imp, pos, cid, self.mpm.collider_body_index, self.state_0.body_q,
                                                                 self.model.body_com, 1.0 / self.frame_dt, self.mpm_wrench])

    def set_targets(self, arm, drum, wheel):
        self.tq[self.coord["front_arm"]] = arm
        self.tq[self.coord["rear_arm"]] = self.home["rear_arm"]
        self.tqd[self.dof["front_drums"]] = drum
        self.tqd[self.dof["rear_drums"]] = 0.0
        for w in WHEELS:
            self.tqd[self.dof[w]] = wheel
        self.control.joint_target_q.assign(self.tq)
        self.control.joint_target_qd.assign(self.tqd)

    def drum_mass(self):
        bq = self.state_0.body_q.numpy()[self.front]
        p, q = bq[:3], bq[3:7]
        x, y, z, w = q
        R = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                      [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                      [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
        local = (self.state_0.particle_q.numpy() - p) @ R
        r = np.hypot(local[:, 0], local[:, 2])
        inside = (r < DRUM_R - 0.002) & (np.abs(local[:, 1]) > DRUM_Y[0]) & (np.abs(local[:, 1]) < DRUM_Y[1])
        return float(inside.sum() * self.particle_mass)

    def update(self):
        t = self.sim_time
        cur = [p for p in self.plan if p[0] <= t][-1]
        name, t0, dur = cur[1], cur[0], cur[2]
        if name != self.phase:
            if self.phase in ("lift", "weigh", "dump", "dig", "fill", "transit"):
                self.collected[self.phase] = self.drum_mass()
            self.phase = name
            print(f"[{t:5.1f} s] {name}  drum load {self.drum_mass():.2f} kg")
        s = smoothstep((t - t0) / dur) if dur else 1.0
        v = self.args.drive_speed / WHEEL_R
        w = self.args.drum_speed
        home = self.home["front_arm"]
        if name == "carry":
            self.set_targets(home, 0.0, 0.0)
        elif name == "lower":
            self.set_targets(home + (self.dig_q - home) * s, w * s, 0.0)
        elif name == "dig":
            dither = self.args.dither_amp * math.sin(2 * math.pi * self.args.dither_hz * (t - t0)) if self.args.dither_hz > 0 else 0.0
            self.set_targets(self.dig_q + max(0.0, dither), w, v * smoothstep((t - t0) / 1.0))
        elif name == "fill":
            self.set_targets(self.dig_q, w, self.args.fill_speed / WHEEL_R * smoothstep((t - t0) / 1.0))
        elif name == "transit":
            ramp = min(smoothstep((t - t0) / 1.0), smoothstep((t0 + dur - t) / 1.0))
            self.set_targets(self.carry_q, 0.3 * w, self.args.transit_speed / WHEEL_R * ramp)
        elif name == "lift":
            self.set_targets(self.dig_q + (self.carry_q - self.dig_q) * s, w * (1 - 0.7 * s), 0.0)
        elif name == "weigh":
            self.set_targets(self.carry_q, 0.3 * w * (1 - s), 0.0)
        elif name == "dump":
            self.set_targets(self.carry_q, -w, 0.0)
        else:
            self.set_targets(self.carry_q, 0.0, 0.0)

    def step(self):
        self.update()
        if self.graph:
            wp.capture_launch(self.graph)
        else:
            self.simulate_rover()
        self.simulate_regolith()
        self.sim_time += self.frame_dt
        self.frame += 1
        if self.record is not None and self.frame % self.args.record_every == 0:
            self.record["body_q"].append(self.state_0.body_q.numpy()[: len(self.blabels)].copy())
            pq = (self.state_0.particle_q.numpy() - REC_LO) / (REC_HI - REC_LO)
            self.record["particle_q"].append(np.round(np.clip(pq, 0.0, 1.0) * 65535).astype(np.uint16))
            self.record["t"].append(self.sim_time)
            self.record["phase"].append(self.phase)
        if self.frame % 60 == 0 and self.phase in ("dig", "fill", "lift", "transit"):
            print(f"[{self.sim_time:5.1f} s] {self.phase}: chassis x {self.state_0.body_q.numpy()[0][0]:+.3f} m, drum load {self.drum_mass():.2f} kg")

    def save_record(self):
        if self.record is None or not self.record["t"]:
            return
        np.savez(self.args.record, body_q=np.array(self.record["body_q"]), particle_q=np.array(self.record["particle_q"]),
                 t=np.array(self.record["t"]), phase=np.array(self.record["phase"]), bodies=np.array(self.blabels), rec_lo=REC_LO,
                 rec_hi=REC_HI, particle_radius=float(self.model.particle_radius.numpy()[0]), particle_mass=self.particle_mass)
        print(f"recorded {len(self.record['t'])} frames -> {self.args.record}")

    def test_final(self):
        self.save_record()
        picked = self.collected.get("weigh", 0.0)
        left = self.drum_mass()
        print(f"[test] collected {picked:.2f} kg after lifting, {left:.2f} kg left after dumping")
        assert picked > self.args.min_load, f"collected only {picked:.2f} kg (need > {self.args.min_load} kg)"
        assert left < 0.5 * picked, f"dumping left {left:.2f} of {picked:.2f} kg in the drums"
        tilt = self.state_0.body_q.numpy()[0][3:7]
        assert abs(tilt[0]) < 0.2 and abs(tilt[1]) < 0.2, "rover tipped"

    def render(self):
        self.viewer.begin_frame(self.sim_time)
        self.viewer.log_state(self.state_0)
        self.viewer.end_frame()

    @staticmethod
    def create_parser():
        parser = newton.examples.create_parser()
        parser.add_argument("--usd", default=None, help="Explicit path to the IPEx USD.")
        parser.add_argument("--variants", default="", help="Variant selections, e.g. Payload=empty")
        parser.add_argument("--substeps", type=int, default=10, help="MuJoCo substeps per 60 Hz frame.")
        parser.add_argument("--earth", action="store_true", help="Earth gravity.")
        parser.add_argument("--two-way", action="store_true", help="Feed regolith reaction impulses back into the rover (lagged by one frame).")
        parser.add_argument("--voxel-size", type=float, default=0.01, help="MPM grid voxel [m]; keep it under a third of the 33 mm scoop mouth.")
        parser.add_argument("--particles-per-cell", type=float, default=2.0, help="Particles per voxel along each axis.")
        parser.add_argument("--bed-start", type=float, default=0.80, help="Regolith bed start, ahead of the front drums [m].")
        parser.add_argument("--bed-length", type=float, default=0.90, help="Regolith bed length [m].")
        parser.add_argument("--bed-half-width", type=float, default=0.36, help="Regolith bed half width [m].")
        parser.add_argument("--bed-depth", type=float, default=0.06, help="Regolith bed depth over rigid ground [m].")
        parser.add_argument("--dig-depth", type=float, default=0.02, help="Cut depth below the bed surface [m]; KSC keeps it under half the 34 mm scoop height.")
        parser.add_argument("--drive-speed", type=float, default=0.05, help="Forward speed while digging [m/s].")
        parser.add_argument("--drum-speed", type=float, default=1.3, help="Drum speed [rad/s]; 1.3 is 12.5 rpm, the actuator maximum.")
        parser.add_argument("--carry-deg", type=float, default=20.0, help="Front arm angle above the driving pose for carrying and dumping [deg].")
        parser.add_argument("--dig-time", type=float, default=10.0, help="Digging time [s].")
        parser.add_argument("--fill-revs", type=float, default=0.0, help="Extra drum revolutions in place after digging, to top up the drums.")
        parser.add_argument("--fill-speed", type=float, default=0.02, help="Creep speed while topping up, so the drums keep cutting [m/s].")
        parser.add_argument("--transit", type=float, default=0.0, help="Distance to drive with the load before dumping [m].")
        parser.add_argument("--transit-speed", type=float, default=0.15, help="Transit speed [m/s].")
        parser.add_argument("--dump-time", type=float, default=6.0, help="Dumping time [s].")
        parser.add_argument("--density", type=float, default=1700.0, help="Regolith bulk density [kg/m^3]; GRC-1 in the Chrono RASSOR studies.")
        parser.add_argument("--friction-angle", type=float, default=38.0, help="Regolith internal friction angle [deg]; GRC-1 is 35-38.4 in the Chrono RASSOR studies.")
        parser.add_argument("--cohesion", type=float, default=200.0, help="Regolith cohesion (MPM yield stress) [Pa].")
        parser.add_argument("--dither-hz", type=float, default=0.0, help="Front shoulder dither while digging [Hz]; 2.66 Hz per SBEL TR-2024-04, 0 = off.")
        parser.add_argument("--dither-amp", type=float, default=0.04, help="Front shoulder dither amplitude, upward only [rad].")
        parser.add_argument("--dilatancy", type=float, default=0.0, help="MPM dilatancy, 0 to 1.")
        parser.add_argument("--young-modulus", type=float, default=1.0e15, help="Particle Young's modulus [Pa]; the default is rigid-plastic.")
        parser.add_argument("--poisson", type=float, default=0.3, help="Particle Poisson ratio.")
        parser.add_argument("--record", default=None, help="Save body poses and particle positions to this .npz (written at the end of a --test run).")
        parser.add_argument("--record-every", type=int, default=2, help="Record every N frames (2 = 30 fps).")
        parser.add_argument("--min-load", type=float, default=2.0, help="Test: minimum regolith collected by the front drums [kg].")
        return parser


if __name__ == "__main__":
    parser = Example.create_parser()
    viewer, args = newton.examples.init(parser)
    if wp.get_device().is_cpu:
        raise SystemExit("this example needs a CUDA GPU")
    newton.examples.run(Example(viewer, args), args)
