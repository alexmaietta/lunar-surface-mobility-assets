import argparse
import glob
import json
import math
import os
import re
import sys
import time as wallclock

import pychrono as chrono

from demo_robot_rover import G_MOON, HULL, REPO, TerminalKeys, UrdfRobot, find_urdf, vec

STAGE = re.compile(r"_(stage\d+|inner|compression|tension\d+|outer|piston)$")
CRUSH_DAMPING = 500.0


def landers():
    sys.path.insert(0, os.path.join(REPO, "scripts"))
    import assetcfg

    return [a for a in (os.path.splitext(os.path.basename(p))[0] for p in sorted(glob.glob(os.path.join(REPO, "configs", "*.py"))))
            if assetcfg.load(a).ASSET_PATH.endswith("/lander")]


def crush_loads(asset):
    sys.path.insert(0, os.path.join(REPO, "scripts"))
    import assetcfg

    variants = getattr(assetcfg.load(asset), "JOINT_VARIANTS", {}).get("LandingGear", {}).get("crush", {})
    return [(re.compile(pat), o["stage_load"], o.get("limit")) for pat, o in variants.items() if o.get("stage_load")]


def subtree_mass(robot, link):
    children = [j.find("child").get("link") for j in robot.xjoints.values() if j.find("parent").get("link") == link]
    b = robot.body(link)
    return (b.GetMass() if b is not None else 0.0) + sum(subtree_mass(robot, c) for c in children)


class Gear:
    def __init__(self, robot, name, mode, load, limit, dt):
        xj = robot.xjoints[name]
        self.name = name
        self.parent, self.child = robot.body(xj.find("parent").get("link")), robot.body(xj.find("child").get("link"))
        self.link = chrono.CastToChLinkLockPrismatic(robot.system.SearchLink(name))
        axis = self.child.GetFrameRefToAbs().TransformDirectionLocalToParent(vec(robot.axis(name)))
        z2 = self.link.GetFrame2Abs().GetRotMat().GetAxisZ()
        body1_is_child = (self.link.GetBody1().GetPos() - self.child.GetPos()).Length() < 1e-9
        self.s = (1.0 if axis.Dot(z2) > 0 else -1.0) * (1.0 if body1_is_child else -1.0)
        lim = xj.find("limit")
        lo, hi = limit or (float(lim.get("lower", 0.0)), float(lim.get("upper", 0.0)))
        self.lo, self.hi = lo, hi
        self.link.LimitRz().SetActive(False)
        lz = self.link.LimitZ()
        lz.SetActive(True)
        lz.SetMin(min(self.s * lo, self.s * hi))
        lz.SetMax(max(self.s * lo, self.s * hi))
        drive = robot.meta["joints"][name].get("drive") or {}
        self.mode, self.load = mode, load
        self.k, self.c = drive.get("stiffness", 0.0), drive.get("damping", 0.0)
        m = subtree_mass(robot, xj.find("child").get("link"))
        self.k_crush = min(load / 0.002, m * (0.5 / dt) ** 2) if load else 0.0
        self.q_rest = 0.0
        self.fz = self.link.ForceZ()
        self.fz.SetActive(True)

    def q(self):
        return self.s * self.link.GetRelCoordsys().pos.z

    def qd(self):
        return self.s * self.link.GetRelCoordsysDt().pos.z

    def reset(self):
        self.q_rest = 0.0
        self.fz.SetActuatorForceTorque(0.0)

    def update(self):
        q, qd = self.q(), self.qd()
        if self.mode == "crush":
            f = self.k_crush * (q - self.q_rest)
            if abs(f) > self.load:
                self.q_rest = q - math.copysign(self.load / self.k_crush, f)
                f = math.copysign(self.load, f)
            force = -f - CRUSH_DAMPING * qd
        else:
            force = -self.k * q - self.c * qd
        self.fz.SetActuatorForceTorque(self.s * force)


class Lander:
    def __init__(self, system, urdf, offset, args, material, crush):
        a = args
        import xml.etree.ElementTree as ET

        hulls = {l.get("name"): HULL for l in ET.parse(urdf).getroot().findall("link") if l.find("collision") is not None}
        self.robot = UrdfRobot(system, urdf, chrono.ChFramed(offset, chrono.QUNIT), material=material, collision_types=hulls,
                               passive_roles=("landing_gear",))
        self.root = self.robot.chassis
        self.bodies = [system.SearchBody(n) for n in self.robot.xlinks if system.SearchBody(n) is not None]
        self.bodies = [b for b in self.bodies if not b.IsFixed()]
        gear = [n for n, j in self.robot.meta["joints"].items() if j["role"] == "landing_gear" and self.robot.xjoints.get(n) is not None
                and self.robot.xjoints[n].get("type") == "prismatic"]
        self.gear = []
        for n in gear:
            hit = next(((load, lim) for pat, load, lim in crush if pat.fullmatch(n)), None) if a.gear == "crush" else None
            load = a.crush_load * 1000 if a.crush_load else (hit[0] if hit else 0.0)
            self.gear.append(Gear(self.robot, n, "crush" if a.gear == "crush" else "spring", load, hit[1] if hit else None, a.step))
        self.groups = {}
        for g in self.gear:
            self.groups.setdefault(STAGE.sub("", g.name), []).append(g)
        lift = a.height - self.lowest_point()
        for b in self.bodies:
            b.SetPos(b.GetPos() + chrono.ChVector3d(0, 0, lift))
        self.home = [(b, chrono.ChVector3d(b.GetPos()), chrono.ChQuaterniond(b.GetRot())) for b in self.bodies]
        self.exits = []
        tj = os.path.join(os.path.dirname(os.path.dirname(urdf)), "usd", "thrusters.json")
        for th in json.load(open(tj))["thrusters"] if os.path.exists(tj) else []:
            if th["kind"] == "main" and system.SearchBody(th["link"]) is not None:
                b = system.SearchBody(th["link"])
                world = offset + vec(th["exit_center_m"]) + chrono.ChVector3d(0, 0, lift)
                self.exits.append((b, b.GetFrameRefToAbs().TransformPointParentToLocal(world)))
        self.mass = sum(b.GetMass() for b in self.bodies)

    def lowest_point(self):
        low = math.inf
        for name, xl in self.robot.xlinks.items():
            for col in xl.findall("collision"):
                mesh = col.find("geometry/mesh")
                if mesh is None:
                    continue
                o = col.find("origin")
                off = vec(o.get("xyz", "0 0 0").split()) if o is not None else chrono.ChVector3d(0, 0, 0)
                frame = self.robot.body(name).GetFrameRefToAbs()
                with open(os.path.join(os.path.dirname(self.robot.urdf), mesh.get("filename"))) as f:
                    for line in f:
                        if line.startswith("v "):
                            low = min(low, frame.TransformPointLocalToParent(vec(line.split()[1:4]) + off).z)
        return low

    def drop(self, v):
        for b, p, q in self.home:
            b.SetPos(p)
            b.SetRot(q)
            b.SetPosDt(v)
            b.SetAngVelParent(chrono.ChVector3d(0, 0, 0))
        for g in self.gear:
            g.reset()
        self.peak = {k: 0.0 for k in self.groups}
        self.peak_tilt = 0.0
        self.clear = math.inf

    def travel(self):
        return {k: sum(g.q() for g in gs) for k, gs in self.groups.items()}

    def tilt(self):
        return math.degrees(math.acos(max(-1.0, min(1.0, self.root.GetRot().GetAxisZ().z))))

    def track(self):
        for k, t in self.travel().items():
            if abs(t) > abs(self.peak[k]):
                self.peak[k] = t
        self.peak_tilt = max(self.peak_tilt, self.tilt())
        for b, local in self.exits:
            self.clear = min(self.clear, b.GetFrameRefToAbs().TransformPointLocalToParent(local).z)


class Example:
    def __init__(self, args):
        a = self.args = args
        self.step_size = a.step
        self.sim_time = self.since_drop = 0.0
        self.frame = 0
        self.system = sys_ = chrono.ChSystemNSC()
        sys_.SetCollisionSystemType(chrono.ChCollisionSystem.Type_BULLET)
        sl = math.radians(a.slope)
        g = 9.81 if a.earth else G_MOON
        sys_.SetGravitationalAcceleration(chrono.ChVector3d(-g * math.sin(sl), 0, -g * math.cos(sl)))
        sys_.SetSolverType(chrono.ChSolver.Type_BARZILAIBORWEIN)
        sys_.GetSolver().AsIterative().SetMaxIterations(200)
        sys_.SetMaxPenetrationRecoverySpeed(0.2)
        chrono.ChCollisionModel.SetDefaultSuggestedEnvelope(0.01)
        chrono.ChCollisionModel.SetDefaultSuggestedMargin(0.005)
        self.mat = chrono.ChContactMaterialData()
        self.mat.mu, self.mat.cr = a.mu, 0.0
        self.urdf = a.urdf or find_urdf(a.asset)
        crush = crush_loads(a.asset) if a.gear == "crush" and not a.urdf else []
        if a.gear == "crush" and not crush and not a.crush_load:
            raise SystemExit(f"{a.asset} has no crush-core variant in its config; pass --crush-load [kN] or use --gear spring")
        n = a.world_count
        self.sink = [a.vz + (a.vz_max - a.vz) * i / max(n - 1, 1) if a.vz_max else a.vz for i in range(n)]
        self.landers = [Lander(sys_, self.urdf, chrono.ChVector3d(i * a.spacing, 0, 0), a, self.mat, crush) for i in range(n)]
        span = (n - 1) * a.spacing
        ground = chrono.ChBodyEasyBox(span + 30, 30, 0.4, 1000, True, True, self.mat.CreateMaterial(sys_.GetContactMethod()))
        ground.SetPos(chrono.ChVector3d(span / 2, 0, -0.2))
        ground.SetFixed(True)
        ground.GetVisualShape(0).SetTexture(chrono.GetChronoDataFile("textures/concrete.jpg"), (span + 30) / 4, 30 / 4)
        ground.GetVisualShape(0).SetColor(chrono.ChColor(0.55, 0.54, 0.52))
        sys_.Add(ground)
        if not self.landers[0].gear:
            raise SystemExit(f"{a.asset}: no prismatic landing_gear joints")
        self.drop()
        l0 = self.landers[0]
        modes = {g.mode for g in l0.gear}
        loads = sorted({round(g.load / 1000, 1) for g in l0.gear if g.load})
        print(f"{os.path.basename(self.urdf)}: {l0.mass:.0f} kg, {len(l0.groups)} struts ({len(l0.gear)} gear joints, "
              + (f"crush {'/'.join(map(str, loads))} kN" if "crush" in modes else "springs") + f"), slope {a.slope:.1f} deg, {n} lander(s)")
        print("sink rates m/s: " + " ".join(f"{v:.2f}" for v in self.sink) + f", drift {a.vh:.2f} m/s at {a.heading:.0f} deg")
        self.keys = TerminalKeys() if a.vis != "none" else None
        if self.keys:
            print("keys (in this terminal): r re-drop")
        self.vis = self.create_vis() if a.vis != "none" else None

    def drop(self):
        a = self.args
        h = math.radians(a.heading)
        for lander, vz in zip(self.landers, self.sink):
            lander.drop(chrono.ChVector3d(a.vh * math.cos(h), a.vh * math.sin(h), -vz))
        self.since_drop = 0.0

    def create_vis(self):
        a = self.args
        span = (len(self.landers) - 1) * a.spacing
        target = chrono.ChVector3d(span / 2, 0, 2.0)
        eye = target + chrono.ChVector3d(-6 - span * 0.3, -12 - span * 0.6, 4)
        if a.vis == "irrlicht":
            import pychrono.irrlicht as irr

            vis = irr.ChVisualSystemIrrlicht()
            vis.AttachSystem(self.system)
            vis.SetCameraVertical(chrono.CameraVerticalDir_Z)
            vis.SetWindowSize(1600, 900)
            vis.SetWindowTitle(f"{a.asset} touchdown - Chrono")
            vis.Initialize()
            vis.AddSkyBox()
            vis.AddCamera(eye, target)
            vis.AddTypicalLights()
            return vis
        import pychrono.vsg3d as vsg

        vis = vsg.ChVisualSystemVSG()
        vis.AttachSystem(self.system)
        vis.SetCameraVertical(chrono.CameraVerticalDir_Z)
        vis.SetWindowSize(1600, 900)
        vis.SetWindowTitle(f"{a.asset} touchdown - Chrono")
        vis.AddCamera(eye, target)
        vis.SetBackgroundColor(chrono.ChColor(0.02, 0.02, 0.03))
        vis.SetLightDirection(math.radians(a.sun_az), math.radians(a.sun_el))
        vis.SetLightIntensity(1.2)
        vis.EnableShadows(a.shadows)
        vis.Initialize()
        return vis

    def step(self):
        if (self.keys and "r" in self.keys.read()) or (self.args.loop and self.since_drop >= self.args.loop):
            self.drop()
        for lander in self.landers:
            for g in lander.gear:
                g.update()
        self.system.DoStepDynamics(self.step_size)
        self.sim_time += self.step_size
        self.since_drop += self.step_size
        self.frame += 1
        for lander in self.landers:
            lander.track()

    def status(self):
        return f"t {self.since_drop:5.2f} s  " + "  ".join(
            f"[{i}] z {l.root.GetPos().z:+5.2f} tilt {l.tilt():4.1f} stroke {max(l.travel().values(), key=abs) * 1000:+5.0f} mm"
            for i, l in enumerate(self.landers))

    def run(self):
        a = self.args
        render_every = max(1, round(1.0 / (60.0 * self.step_size)))
        t0 = wallclock.perf_counter()
        timer = chrono.ChRealtimeStepTimer()
        try:
            while a.time <= 0 or self.sim_time < a.time:
                if self.vis is not None:
                    if not self.vis.Run():
                        break
                    if self.frame % render_every == 0:
                        self.vis.BeginScene()
                        self.vis.Render()
                        self.vis.EndScene()
                self.step()
                if self.vis is not None and not a.fast:
                    timer.Spin(self.step_size)
                if self.frame % round(0.5 / self.step_size) == 0:
                    print(self.status())
        finally:
            if self.keys:
                self.keys.close()
        wall = wallclock.perf_counter() - t0
        print(f"\nsimulated {self.sim_time:.2f} s in {wall:.1f} s wall (RTF {wall / max(self.sim_time, 1e-9):.2f})")
        self.report()
        if a.test:
            self.test_final()

    def report(self):
        for i, (l, vz) in enumerate(zip(self.landers, self.sink)):
            final = l.travel()
            print(f"lander {i}: sink {vz:.2f} m/s, peak tilt {l.peak_tilt:.1f} deg, final tilt {l.tilt():.2f} deg"
                  + (f", min nozzle clearance {l.clear:.3f} m" if l.exits else ""))
            for k in l.groups:
                print(f"  {k:24s} peak {l.peak[k] * 1000:+7.1f} mm  final {final[k] * 1000:+7.1f} mm")

    def test_final(self):
        z = [l.root.GetPos().z for l in self.landers]
        tilt = [l.tilt() for l in self.landers]
        stroke = [max(abs(v) for v in l.peak.values()) for l in self.landers]
        checks = {"landers stayed above the surface": all(v > -0.5 for v in z), "landers upright (tilt < 10 deg)": all(t < 10.0 for t in tilt),
                  "gear stroked on touchdown": all(s > 0.002 for s in stroke),
                  "gear stayed within its stroke": all(abs(l.peak[k]) <= sum(g.hi - g.lo for g in gs) + 0.01
                                                       for l in self.landers for k, gs in l.groups.items())}
        for k, ok in checks.items():
            print(f"[{'ok' if ok else 'FAIL'}] {k}")
        assert all(checks.values()), "lander touchdown checks failed"

    @staticmethod
    def create_parser():
        parser = argparse.ArgumentParser(description="Drop a lunar lander URDF onto the surface in Project Chrono.")
        parser.add_argument("--asset", default="apollo_lm", help=f"Lander asset id ({', '.join(landers())}).")
        parser.add_argument("--urdf", default=None, help="Explicit path to a lander URDF.")
        parser.add_argument("--vis", default="vsg", choices=["vsg", "irrlicht", "none"], help="Run-time visualisation.")
        parser.add_argument("--gear", default="spring", choices=["spring", "crush"],
                            help="spring (the URDF gear) or crush (crush-core stages from the asset config, or --crush-load).")
        parser.add_argument("--crush-load", type=float, default=0.0, help="Crush load for every gear joint [kN]; overrides the config.")
        parser.add_argument("--world-count", type=int, default=1, help="Number of landers side by side.")
        parser.add_argument("--vz", type=float, default=1.0, help="Sink rate at touchdown [m/s] (first lander).")
        parser.add_argument("--vz-max", type=float, default=0.0, help="Sink rate of the last lander; landers sweep vz..vz-max.")
        parser.add_argument("--vh", type=float, default=0.3, help="Horizontal drift [m/s].")
        parser.add_argument("--heading", type=float, default=0.0, help="Drift direction [deg from +X].")
        parser.add_argument("--slope", type=float, default=0.0, help="Surface slope [deg], downhill along +X.")
        parser.add_argument("--height", type=float, default=0.02, help="Footpad height above the surface at release [m].")
        parser.add_argument("--mu", type=float, default=0.8, help="Footpad-surface friction.")
        parser.add_argument("--spacing", type=float, default=12.0, help="Distance between landers [m].")
        parser.add_argument("--loop", type=float, default=0.0, help="Re-drop automatically every N seconds (0 = off).")
        parser.add_argument("--step", type=float, default=1e-3, help="Integration step [s].")
        parser.add_argument("--time", type=float, default=0.0, help="Stop after this many simulated seconds (0 = run until closed).")
        parser.add_argument("--earth", action="store_true", help="Earth gravity.")
        parser.add_argument("--shadows", action="store_true", help="VSG shadows.")
        parser.add_argument("--sun-az", type=float, default=60.0, help="Sun azimuth [deg].")
        parser.add_argument("--sun-el", type=float, default=12.0, help="Sun elevation [deg].")
        parser.add_argument("--fast", action="store_true", help="Run as fast as possible instead of real time.")
        parser.add_argument("--test", action="store_true", help="Run checks at the end.")
        return parser


if __name__ == "__main__":
    Example(Example.create_parser().parse_args()).run()
