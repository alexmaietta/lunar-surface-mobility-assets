import argparse
import math
import os
import sys
import time as wallclock

import numpy as np
import pychrono as chrono
import pychrono.fsi as fsi
import pychrono.vehicle as veh

from demo_robot_rover import G_MOON, HULL, REPO, UrdfRobot, find_urdf, smoothstep, vec

sys.path.insert(0, os.path.join(REPO, "scripts"))
import assetcfg

CFG = assetcfg.load("ipex")
SHOULDER_X, SHOULDER_Z = CFG.SHOULDER
ARM_LEN, ARM_POSE = CFG.ARM_LEN, CFG.ARM_POSE
DRUM_R, DRUM_Y = CFG.DRUM_R, CFG.DRUM_Y
WHEEL_R = CFG.R_W - CFG.GROUSER_H / 2
WHEELS = ("fl_wheel", "fr_wheel", "rl_wheel", "rr_wheel")
FSI_BODIES = ("front_drums", "fl_wheel", "fr_wheel")


def arm_angle(drum_bottom_z, ride_z):
    zc = drum_bottom_z + DRUM_R - ride_z
    return math.asin(max(-1.0, min(1.0, (zc - SHOULDER_Z) / ARM_LEN))) - ARM_POSE


def obj_parts(path):
    verts, parts = [], []
    with open(path) as f:
        for line in f:
            if line.startswith("v "):
                verts.append([float(v) for v in line.split()[1:4]])
            elif line.startswith("o ") or line.startswith("g ") or (line.startswith("f ") and not parts):
                parts.append([])
                if line.startswith("f "):
                    parts[-1].append([int(t.split("/")[0]) - 1 for t in line.split()[1:4]])
            elif line.startswith("f "):
                parts[-1].append([int(t.split("/")[0]) - 1 for t in line.split()[1:4]])
    v = np.array(verts)
    return [v[np.array(tris)] for tris in parts if tris]


def bce_markers(path, spacing, dilate, shell):
    out = []
    for tris in obj_parts(path):
        n = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
        keep = np.linalg.norm(n, axis=1) > 1e-12
        n = n[keep] / np.linalg.norm(n[keep], axis=1)[:, None]
        d = np.einsum("ij,ij->i", n, tris[keep, 0])
        c = tris.reshape(-1, 3).mean(axis=0)
        flip = n @ c - d > 0
        n[flip], d[flip] = -n[flip], -d[flip]
        lo = np.floor((tris.reshape(-1, 3).min(axis=0) - dilate) / spacing)
        hi = np.ceil((tris.reshape(-1, 3).max(axis=0) + dilate) / spacing)
        axes = [np.arange(a, b + 1) * spacing for a, b in zip(lo, hi)]
        pts = np.stack(np.meshgrid(*axes, indexing="ij"), axis=-1).reshape(-1, 3)
        dist = (pts @ n.T - d).max(axis=1)
        inside = (dist <= dilate) & (dist >= -shell)
        out.append(pts[inside])
    pts = np.concatenate(out) if out else np.zeros((0, 3))
    return np.unique(np.round(pts / spacing).astype(np.int64), axis=0) * spacing


class Example:
    def __init__(self, args):
        a = self.args = args
        self.sim_time, self.frame = 0.0, 0
        self.exchange = a.step * a.substeps
        g = 9.81 if a.earth else G_MOON
        self.system = sys_ = chrono.ChSystemNSC()
        sys_.SetCollisionSystemType(chrono.ChCollisionSystem.Type_BULLET)
        sys_.SetGravitationalAcceleration(chrono.ChVector3d(0, 0, -g))
        sys_.SetSolverType(chrono.ChSolver.Type_BARZILAIBORWEIN)
        sys_.GetSolver().AsIterative().SetMaxIterations(150)
        sys_.SetMaxPenetrationRecoverySpeed(0.2)
        chrono.ChCollisionModel.SetDefaultSuggestedEnvelope(0.005)
        chrono.ChCollisionModel.SetDefaultSuggestedMargin(0.002)
        self.mat = chrono.ChContactMaterialData()
        self.mat.mu, self.mat.cr = 0.8, 0.0
        ground = chrono.ChBodyEasyBox(8, 4, 0.2, 1000, True, True, self.mat.CreateMaterial(sys_.GetContactMethod()))
        ground.SetPos(chrono.ChVector3d(1.0, 0, -0.1))
        ground.SetFixed(True)
        ground.GetVisualShape(0).SetColor(chrono.ChColor(0.42, 0.41, 0.39))
        sys_.Add(ground)

        self.urdf = a.urdf or find_urdf("ipex")
        hulls = {n: HULL for n in ("chassis", *WHEELS)}
        self.robot = UrdfRobot(sys_, self.urdf, chrono.ChFramed(chrono.ChVector3d(0, 0, 0.02), chrono.QUNIT), "speed", self.mat, hulls)
        self.chassis = self.robot.chassis
        for n in ("front_arm", "rear_arm"):
            self.robot.joints[n].rate = 3.0
        self.front = self.robot.body("front_drums")

        s = a.spacing
        self.terrain = terrain = veh.CRMTerrain(sys_, s)
        terrain.SetVerbose(a.verbose)
        terrain.SetGravitationalAcceleration(chrono.ChVector3d(0, 0, -g))
        terrain.SetStepSizeCFD(a.step)
        terrain.SetStepsizeMBD(a.step)
        soil = fsi.ElasticMaterialProperties()
        soil.density = a.density
        soil.Young_modulus = a.young_modulus
        soil.Poisson_ratio = a.poisson
        soil.mu_I0 = 0.04
        soil.mu_fric_s = soil.mu_fric_2 = math.tan(math.radians(a.friction_angle))
        soil.average_diam = a.grain
        soil.cohesion_coeff = a.cohesion
        terrain.SetElasticSPH(soil)
        sph = fsi.SPHParameters()
        sph.integration_scheme = fsi.IntegrationScheme_RK2
        sph.initial_spacing = s
        sph.d0_multiplier = 1.2
        sph.free_surface_threshold = 2.0
        sph.artificial_viscosity = 0.5
        sph.use_consistent_gradient_discretization = False
        sph.use_consistent_laplacian_discretization = False
        sph.viscosity_method = fsi.ViscosityMethod_ARTIFICIAL_BILATERAL
        sph.boundary_method = fsi.BoundaryMethod_ADAMI
        sph.use_variable_time_step = True
        terrain.SetSPHParameters(sph)
        terrain.SetOutputLevel(fsi.OutputLevel_STATE)

        self.bce = 0
        for name in FSI_BODIES:
            body = self.robot.body(name)
            mesh = self.robot.xlinks[name].find("collision/geometry/mesh")
            pts = bce_markers(os.path.join(os.path.dirname(self.urdf), mesh.get("filename")), s, a.bce_dilate * s, 2.0 * s)
            ref, com = body.GetFrameRefToAbs(), body.GetFrameCOMToAbs()
            markers = chrono.vector_ChVector3d()
            for p in pts:
                markers.append(com.TransformPointParentToLocal(ref.TransformPointLocalToParent(vec(p))))
            terrain.GetFsiSystemSPH().AddFsiBody(body, markers, chrono.ChFramed(), False)
            self.bce += len(pts)
        self.bed_lo = np.array([a.bed_start, -a.bed_half_width, 0.0])
        self.bed_hi = np.array([a.bed_start + a.bed_length, a.bed_half_width, a.bed_depth])
        terrain.Construct(chrono.ChVector3d(a.bed_length, 2 * a.bed_half_width, a.bed_depth),
                          chrono.ChVector3d(a.bed_start + a.bed_length / 2, 0, 0), fsi.BoxSide_Z_NEG)
        lo = chrono.ChVector3d(-0.1, -a.bed_half_width - 0.3, -0.1)
        hi = chrono.ChVector3d(a.bed_start + a.bed_length + 0.3, a.bed_half_width + 0.3, 0.6)
        terrain.SetComputationalDomain(chrono.ChAABB(lo, hi))
        if a.active_domain and min(a.active_domain) > 0:
            terrain.SetActiveDomain(chrono.ChVector3d(*a.active_domain))
        terrain.Initialize()
        self.sph = terrain.GetFluidSystemSPH()
        self.particle_mass = a.density * s ** 3
        self.bed_mass = self.particle_mass * terrain.GetNumSPHParticles()

        self.home = {n: self.robot.joints[n].target for n in ("front_arm", "rear_arm")}
        self.dig_q = arm_angle(a.bed_depth - a.dig_depth, 0.004)
        self.carry_q = math.radians(a.carry_deg)
        phases = [("carry", 1.0), ("lower", 2.0), ("dig", a.dig_time)]
        if a.fill_revs > 0:
            phases.append(("fill", a.fill_revs * 2 * math.pi / a.drum_speed))
        phases.append(("lift", 2.5))
        if a.transit > 0:
            phases.append(("transit", a.transit / a.transit_speed + 1.0))
        phases += [("weigh", 1.5), ("dump", a.dump_time), ("done", 0.0)]
        self.plan, t0 = [], 0.0
        for name, dur in phases:
            self.plan.append((t0, name, dur))
            t0 += dur
        self.duration = t0
        self.phase = "carry"
        self.collected = {}
        bb = terrain.GetSPHBoundingBox()
        print(f"ipex dig (CRM): {terrain.GetNumSPHParticles()} SPH particles, {self.bed_mass:.1f} kg regolith bed "
              f"({bb.min.x:.2f}..{bb.max.x:.2f}, {bb.min.y:.2f}..{bb.max.y:.2f}, {bb.min.z:.3f}..{bb.max.z:.3f} m), "
              f"spacing {s * 1000:.0f} mm, {self.bce} rigid BCE markers on the front drums and wheels")
        print(f"dig depth {a.dig_depth * 100:.1f} cm (front arm {math.degrees(self.dig_q):+.1f} deg), friction angle "
              f"{a.friction_angle:.0f} deg, cohesion {a.cohesion:.0f} Pa, sequence {self.duration:.1f} s")
        self.vis = self.create_vis() if a.vis != "none" else None

    def create_vis(self):
        import pychrono.vsg3d as vsg

        bb = self.terrain.GetSPHBoundingBox()
        vis_fsi = fsi.ChSphVisualizationVSG(self.terrain.GetFsiSystemSPH())
        vis_fsi.EnableFluidMarkers(True)
        vis_fsi.EnableBoundaryMarkers(False)
        vis_fsi.EnableRigidBodyMarkers(self.args.show_bce)
        vis_fsi.SetSPHColorCallback(fsi.ParticleHeightColorCallback(bb.min.z, bb.max.z), chrono.ChColormap.Type_BROWN)
        vis = vsg.ChVisualSystemVSG()
        vis.AttachPlugin(vis_fsi)
        vis.AttachSystem(self.system)
        vis.SetCameraVertical(chrono.CameraVerticalDir_Z)
        vis.SetWindowTitle("IPEx dig on CRM regolith - Chrono")
        vis.SetWindowSize(1600, 900)
        vis.AddCamera(chrono.ChVector3d(0.6, -2.2, 0.9), chrono.ChVector3d(0.9, 0, 0.1))
        vis.SetBackgroundColor(chrono.ChColor(0.02, 0.02, 0.03))
        vis.SetLightIntensity(1.1)
        vis.SetLightDirection(math.radians(60), math.radians(25))
        vis.Initialize()
        self.vis_fsi = vis_fsi
        return vis

    def pos(self):
        return self.chassis.GetFrameRefToAbs().GetPos()

    def set_targets(self, arm, drum, wheel):
        j = self.robot.joints
        j["front_arm"].target = arm
        j["rear_arm"].target = self.home["rear_arm"]
        j["front_drums"].set(drum)
        j["rear_drums"].set(0.0)
        for w in WHEELS:
            j[w].set(wheel)
        self.robot.update_servos(self.exchange)

    def drum_mass(self):
        p = np.asarray(self.sph.GetParticlePositionsNumpy()).reshape(-1, 3)[: self.sph.GetNumFluidMarkers()]
        f = self.front.GetFrameRefToAbs()
        o, r = f.GetPos(), f.GetRotMat()
        rot = np.array([[r.GetAxisX().x, r.GetAxisY().x, r.GetAxisZ().x], [r.GetAxisX().y, r.GetAxisY().y, r.GetAxisZ().y],
                        [r.GetAxisX().z, r.GetAxisY().z, r.GetAxisZ().z]])
        local = (p - np.array([o.x, o.y, o.z])) @ rot
        rad = np.hypot(local[:, 0], local[:, 2])
        inside = (rad < DRUM_R - 0.002) & (np.abs(local[:, 1]) > DRUM_Y[0]) & (np.abs(local[:, 1]) < DRUM_Y[1])
        return float(inside.sum() * self.particle_mass)

    def update(self):
        a, t = self.args, self.sim_time
        t0, name, dur = [p for p in self.plan if p[0] <= t][-1]
        if name != self.phase:
            if self.phase in ("lift", "weigh", "dump", "dig", "fill", "transit"):
                self.collected[self.phase] = self.drum_mass()
            self.phase = name
            print(f"[{t:5.1f} s] {name}  drum load {self.drum_mass():.2f} kg")
        s = smoothstep((t - t0) / dur) if dur else 1.0
        v, w, home = a.drive_speed / WHEEL_R, a.drum_speed, self.home["front_arm"]
        if name == "carry":
            self.set_targets(home, 0.0, 0.0)
        elif name == "lower":
            self.set_targets(home + (self.dig_q - home) * s, w * s, 0.0)
        elif name == "dig":
            dither = a.dither_amp * math.sin(2 * math.pi * a.dither_hz * (t - t0)) if a.dither_hz > 0 else 0.0
            self.set_targets(self.dig_q + max(0.0, dither), w, v * smoothstep((t - t0) / 1.0))
        elif name == "fill":
            self.set_targets(self.dig_q, w, a.fill_speed / WHEEL_R * smoothstep((t - t0) / 1.0))
        elif name == "transit":
            ramp = min(smoothstep((t - t0) / 1.0), smoothstep((t0 + dur - t) / 1.0))
            self.set_targets(self.carry_q, 0.3 * w, a.transit_speed / WHEEL_R * ramp)
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
        self.terrain.DoStepDynamics(self.exchange)
        self.sim_time += self.exchange
        self.frame += 1

    def run(self):
        a = self.args
        end = a.time if a.time > 0 else self.duration + 0.5
        render_every = max(1, round(1.0 / (a.render_fps * self.exchange)))
        report_every = max(1, round(1.0 / self.exchange))
        t0 = wallclock.perf_counter()
        while self.sim_time < end:
            if self.vis is not None:
                if not self.vis.Run():
                    break
                if self.frame % render_every == 0:
                    self.vis.Render()
            self.step()
            if self.frame % report_every == 0:
                p = self.pos()
                print(f"[{self.sim_time:5.1f} s] {self.phase}: chassis x {p.x:+.3f} m, drum load {self.drum_mass():.2f} kg, "
                      f"RTF {(wallclock.perf_counter() - t0) / self.sim_time:.0f}")
        wall = wallclock.perf_counter() - t0
        print(f"\nsimulated {self.sim_time:.2f} s in {wall:.1f} s wall (RTF {wall / max(self.sim_time, 1e-9):.1f})")
        if a.test:
            self.test_final()

    def test_final(self):
        picked = self.collected.get("weigh", 0.0)
        left = self.drum_mass()
        print(f"[test] collected {picked:.2f} kg after lifting, {left:.2f} kg left after dumping")
        up = self.chassis.GetRot().GetAxisZ().z
        checks = {f"collected more than {self.args.min_load} kg": picked > self.args.min_load,
                  "dumping emptied at least half the drums": left < 0.5 * picked, "rover upright": up > 0.95}
        for k, ok in checks.items():
            print(f"[{'ok' if ok else 'FAIL'}] {k}")
        assert all(checks.values()), "ipex dig checks failed"

    @staticmethod
    def create_parser():
        parser = argparse.ArgumentParser(description="IPEx bucket-drum digging into CRM (SPH) regolith in Project Chrono.")
        parser.add_argument("--urdf", default=None, help="Explicit path to the IPEx URDF.")
        parser.add_argument("--vis", default="vsg", choices=["vsg", "none"], help="Run-time visualisation.")
        parser.add_argument("--time", type=float, default=0.0, help="Stop after this many simulated seconds (0 = the whole sequence).")
        parser.add_argument("--step", type=float, default=2.5e-4, help="Initial CFD step and MBD step [s]; the CFD step adapts.")
        parser.add_argument("--substeps", type=int, default=4, help="Steps per FSI exchange (control runs once per exchange).")
        parser.add_argument("--render-fps", type=float, default=30.0, help="Render rate [Hz].")
        parser.add_argument("--earth", action="store_true", help="Earth gravity.")
        parser.add_argument("--spacing", type=float, default=0.006, help="SPH particle spacing [m]; keep it under a third of the 33 mm scoop mouth.")
        parser.add_argument("--bce-dilate", type=float, default=0.75, help="BCE marker shell around each convex collision part [x spacing].")
        parser.add_argument("--active-domain", type=float, nargs=3, default=[0.5, 0.9, 0.5], metavar=("LX", "LY", "LZ"),
                            help="CRM active box around each FSI body [m]; particles outside it are frozen. Pass 0 0 0 to simulate the whole bed.")
        parser.add_argument("--show-bce", action="store_true", help="Draw the rigid-body BCE markers.")
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
        parser.add_argument("--fill-speed", type=float, default=0.02, help="Creep speed while topping up [m/s].")
        parser.add_argument("--transit", type=float, default=0.0, help="Distance to drive with the load before dumping [m].")
        parser.add_argument("--transit-speed", type=float, default=0.15, help="Transit speed [m/s].")
        parser.add_argument("--dump-time", type=float, default=6.0, help="Dumping time [s].")
        parser.add_argument("--density", type=float, default=1700.0, help="Regolith bulk density [kg/m^3]; GRC-1 in the Chrono RASSOR studies.")
        parser.add_argument("--friction-angle", type=float, default=38.0, help="Regolith internal friction angle [deg]; GRC-1 is 35-38.4.")
        parser.add_argument("--cohesion", type=float, default=200.0, help="Regolith cohesion [Pa].")
        parser.add_argument("--young-modulus", type=float, default=1.0e6, help="CRM Young's modulus [Pa].")
        parser.add_argument("--poisson", type=float, default=0.3, help="CRM Poisson ratio.")
        parser.add_argument("--grain", type=float, default=0.005, help="CRM average grain diameter for the mu(I) rheology [m].")
        parser.add_argument("--dither-hz", type=float, default=0.0, help="Front shoulder dither while digging [Hz]; 2.66 Hz per SBEL TR-2024-04, 0 = off.")
        parser.add_argument("--dither-amp", type=float, default=0.04, help="Front shoulder dither amplitude, upward only [rad].")
        parser.add_argument("--min-load", type=float, default=2.0, help="Test: minimum regolith collected by the front drums [kg].")
        parser.add_argument("--verbose", action="store_true", help="Verbose FSI output.")
        parser.add_argument("--test", action="store_true", help="Run checks at the end.")
        return parser


if __name__ == "__main__":
    Example(Example.create_parser().parse_args()).run()
