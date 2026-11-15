import argparse
import glob
import json
import math
import os
import select
import sys
import time as wallclock
import xml.etree.ElementTree as ET

import pychrono as chrono
import pychrono.parsers as parsers

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
G_MOON = 1.625
MODES = ("ackermann", "crab", "spin")
ACT = parsers.ChParserURDF
HULL = ACT.MeshCollisionType_CONVEX_HULL
POSITION_ROLES = {"steer", "arm", "antenna", "camera", "hatch", "tool", "solar", "gimbal", "stair", "latch", "deploy", "railing",
                  "radiator", "crane"}
VELOCITY_ROLES = {"drive", "drill", "excavate"}
SERVO_RATE = {"steer": 1.0, "camera": 0.6, "antenna": 0.4, "hatch": 1.5, "arm": 0.15}
TOGGLES = {"h": "hatch", "t": "stair", "g": "latch"}
ROBOT_FAMILY = 3
MOTOR_SIGN = {"rotation": -1.0, "linear": -1.0}


def find_urdf(asset):
    hits = glob.glob(os.path.join(REPO, "assets", "*", "*", "*", "urdf", f"{asset}.urdf"))
    hits += glob.glob(os.path.join(REPO, "build", asset, "urdf", asset, "urdf", f"{asset}.urdf"))
    if not hits:
        raise SystemExit(f"no URDF for '{asset}': build it with ./pipeline.sh {asset} or pass --urdf")
    return hits[0]


def vec(v):
    return chrono.ChVector3d(*map(float, v))


class Joint:
    def __init__(self, name, link, role, drive, prismatic, limits, effort, actuation):
        link = chrono.CastToChLinkMotorLinear(link) if prismatic else chrono.CastToChLinkMotorRotation(link)
        self.name, self.link, self.role, self.drive, self.prismatic = name, link, role, drive, prismatic
        self.lower, self.upper = limits
        self.effort, self.actuation = effort, actuation
        self.servo = actuation == ACT.ActuationType_POSITION
        self.sign = MOTOR_SIGN["linear" if prismatic else "rotation"]
        self.fun = chrono.ChFunctionSetpoint() if self.servo else chrono.ChFunctionConst(0.0)
        link.SetMotorFunction(self.fun)
        self.target = self.command = float(drive.get("target", 0.0)) if self.servo else 0.0
        self.rate = SERVO_RATE.get(role, 0.5)

    def position(self):
        return self.sign * (self.link.GetMotorPos() if self.prismatic else self.link.GetMotorAngle())

    def velocity(self):
        return self.sign * (self.link.GetMotorPosDt() if self.prismatic else self.link.GetMotorAngleDt())

    def set(self, value, time=0.0):
        if self.servo:
            self.fun.SetSetpoint(self.sign * float(value), time)
        else:
            self.fun.SetConstant(self.sign * float(value))


class UrdfRobot:
    def __init__(self, system, urdf, pose, wheel_actuation="speed", material=None, collision_types=None, passive_roles=()):
        self.system, self.urdf, self.pose = system, urdf, pose
        meta = urdf + ".json"
        self.meta = json.load(open(meta)) if os.path.exists(meta) else {"joints": {}, "loops": []}
        self.xml = ET.parse(urdf).getroot()
        self.xjoints = {j.get("name"): j for j in self.xml.findall("joint")}
        self.xlinks = {l.get("name"): l for l in self.xml.findall("link")}
        self.parser = parser = ACT(urdf)
        if material is not None:
            parser.SetDefaultContactMaterial(material)
        for name, kind in (collision_types or {}).items():
            parser.SetBodyMeshCollisionType(name, kind)
        actuation = {}
        for name, info in self.meta["joints"].items():
            role, kind = info["role"], (info.get("drive") or {}).get("kind")
            if role in passive_roles or name not in self.xjoints or self.xjoints[name].get("type") == "fixed":
                continue
            if role == "drive":
                act = ACT.ActuationType_SPEED if wheel_actuation == "speed" else ACT.ActuationType_FORCE
            elif role == "active_suspension" or kind == "spring":
                act = ACT.ActuationType_FORCE
            elif role in VELOCITY_ROLES or kind == "velocity":
                act = ACT.ActuationType_SPEED
            elif role in POSITION_ROLES or kind == "position":
                act = ACT.ActuationType_POSITION
            else:
                continue
            parser.SetJointActuationType(name, act)
            actuation[name] = act
        parser.SetRootInitPose(pose)
        parser.PopulateSystem(system)
        self.chassis = self._free_root()
        for b in system.GetBodies():
            if b.GetName() not in self.xlinks:
                continue
            cm = b.GetCollisionModel()
            if cm is not None and cm.GetNumShapes() > 0:
                cm.SetFamily(ROBOT_FAMILY)
                cm.DisallowCollisionsWith(ROBOT_FAMILY)
                b.EnableCollision(True)
        self.loops = [self._close_loop(lp) for lp in self.meta.get("loops") or []]
        for name in [n for n in actuation if self.xjoints[n].get("type") == "prismatic"]:
            self._align_linear_motor(name)
        self.joints = {}
        for name, act in actuation.items():
            lim = self.xjoints[name].find("limit")
            get = lambda k, d: float(lim.get(k)) if lim is not None and lim.get(k) is not None else d
            self.joints[name] = Joint(name, parser.GetChMotor(name), self.meta["joints"][name]["role"],
                                      self.meta["joints"][name].get("drive") or {}, self.xjoints[name].get("type") == "prismatic",
                                      (get("lower", -math.inf), get("upper", math.inf)), get("effort", 0.0), act)

    def _free_root(self):
        root = self.parser.GetRootChBody()
        if not root.IsFixed():
            return root
        chassis = root
        for name, j in self.xjoints.items():
            if j.find("parent").get("link") == root.GetName() and j.get("type") == "fixed":
                link = self.system.SearchLink(name)
                if link is not None:
                    self.system.RemoveLink(link)
                chassis = self.parser.GetChBody(j.find("child").get("link"))
        self.system.RemoveBody(root)
        return chassis

    def _close_loop(self, lp):
        parent, child = self.parser.GetChBody(lp["parent"]), self.parser.GetChBody(lp["child"])
        anchor = self.pose.TransformPointLocalToParent(vec(lp["anchor"]))
        if lp["closure"] == "revolute":
            rot = chrono.ChMatrix33d()
            axis = self.pose.TransformDirectionLocalToParent(vec(lp["axis"]))
            rot.SetFromAxisX(axis, chrono.ChVector3d(0, 0, 1) if abs(axis.z) < 0.9 else chrono.ChVector3d(1, 0, 0))
            link = chrono.ChLinkLockPointLine()
            link.Initialize(child, parent, chrono.ChFramed(anchor, rot.GetQuaternion()))
        else:
            link = chrono.ChLinkLockSpherical()
            link.Initialize(child, parent, chrono.ChFramed(anchor, chrono.QUNIT))
        link.SetName(lp["loop"])
        self.system.AddLink(link)
        return link

    def _align_linear_motor(self, name):
        xj = self.xjoints[name]
        parent, child = self.parser.GetChBody(xj.find("parent").get("link")), self.parser.GetChBody(xj.find("child").get("link"))
        ref = child.GetFrameRefToAbs()
        axis = ref.TransformDirectionLocalToParent(vec(self.axis(name)))
        rot = chrono.ChMatrix33d()
        rot.SetFromAxisZ(axis, chrono.ChVector3d(1, 0, 0) if abs(axis.x) < 0.9 else chrono.ChVector3d(0, 1, 0))
        chrono.CastToChLinkMotorLinear(self.parser.GetChMotor(name)).Initialize(parent, child, chrono.ChFramed(ref.GetPos(), rot.GetQuaternion()))

    def body(self, name):
        return self.parser.GetChBody(name)

    def role(self, role):
        return [j for j in self.joints.values() if j.role == role]

    def axis(self, name):
        ax = self.xjoints[name].find("axis")
        return [float(v) for v in (ax.get("xyz") if ax is not None else "1 0 0").split()]

    def collision_radius(self, link_name, axis):
        mesh = self.xlinks[link_name].find("collision/geometry/mesh")
        if mesh is None:
            return None
        r = 0.0
        with open(os.path.join(os.path.dirname(self.urdf), mesh.get("filename"))) as f:
            for line in f:
                if line.startswith("v "):
                    p = [float(v) for v in line.split()[1:4]]
                    along = sum(a * b for a, b in zip(p, axis))
                    r = max(r, math.sqrt(max(0.0, sum(c * c for c in p) - along * along)))
        return r

    def update_servos(self, dt):
        t = self.system.GetChTime() + dt
        for j in self.joints.values():
            if not j.servo:
                continue
            target = min(max(j.target, j.lower), j.upper)
            step = j.rate * dt
            j.command += max(-step, min(step, target - j.command))
            j.set(j.command, t)


def smoothstep(t):
    t = min(1.0, max(0.0, t))
    return t * t * (3 - 2 * t)


class Sequencer:
    def __init__(self, joints):
        self.joints, self.queue, self.active, self.t = joints, [], None, 0.0

    def add(self, steps, **extra):
        for step, dur in steps:
            self.queue.append(dict({k: v for k, v in step.items() if k in self.joints or k.startswith("_")}, _dur=dur, **extra))

    def pending(self):
        return len(self.queue) + (1 if self.active else 0)

    def step(self, dt):
        started = finished = None
        if self.active is None and self.queue:
            started = self.queue.pop(0)
            self.active, self.t = (started, {k: self.joints[k].target for k in started if k in self.joints}), 0.0
        if self.active is not None:
            step, start = self.active
            self.t += dt
            f = smoothstep(self.t / step["_dur"]) if step["_dur"] > 0 else 1.0
            for k, a in start.items():
                self.joints[k].target = a + (step[k] - a) * f
            if f >= 1.0:
                self.active, finished = None, step
        return started, finished


class RoverDriver:
    motor_type = "speed"

    def __init__(self, max_speed=10.0, max_steer=math.radians(45)):
        self.max_speed, self.max_steer = max_speed, max_steer
        self.speed, self.steer, self.mode, self.ride = 0.0, 0.0, "ackermann", 0.0
        self.lift = {}

    def SetSpeed(self, kmh):
        self.speed = max(-self.max_speed, min(self.max_speed, kmh))

    def SetSteering(self, angle):
        self.steer = max(-self.max_steer, min(self.max_steer, angle))

    def SetMode(self, mode):
        self.mode = mode

    def SetLifting(self, angle, corner=None):
        if corner is None:
            self.ride = angle
        else:
            self.lift[corner] = angle

    def Synchronize(self, time):
        pass

    def wheel_torque(self, omega_target, omega):
        return 0.0

    def close(self):
        pass


class SpeedDriver(RoverDriver):
    def __init__(self, speed=0.0, ramp_time=1.0, **kw):
        super().__init__(**kw)
        self.cruise, self.ramp_time = speed, ramp_time

    def Synchronize(self, time):
        self.SetSpeed(self.cruise * (min(1.0, time / self.ramp_time) if self.ramp_time > 0 else 1.0))


class DCMotorDriver(SpeedDriver):
    motor_type = "torque"

    def __init__(self, stall_torque=54.5, no_load_speed=1.2, **kw):
        super().__init__(**kw)
        self.stall_torque, self.no_load_speed = stall_torque, no_load_speed

    def SetMotorStallTorque(self, torque):
        self.stall_torque = torque

    def SetMotorNoLoadSpeed(self, speed):
        self.no_load_speed = speed

    def wheel_torque(self, omega_target, omega):
        u = max(-1.0, min(1.0, omega_target / self.no_load_speed))
        tau = self.stall_torque * (u - omega / self.no_load_speed)
        return max(-self.stall_torque, min(self.stall_torque, tau))


class ScriptedDriver(RoverDriver):
    def __init__(self, script, **kw):
        super().__init__(**kw)
        self.script = sorted(script, key=lambda e: e[0])
        self.events = []

    def Synchronize(self, time):
        while self.script and time >= self.script[0][0]:
            _, kind, arg = self.script.pop(0)
            if kind == "drive":
                self.SetSpeed(arg[0])
                self.SetSteering(arg[1])
            elif kind == "mode":
                self.SetMode(arg)
            elif kind == "ride":
                self.SetLifting(arg)
            else:
                self.events.append((kind, arg))


class TerminalKeys:
    def __init__(self):
        self.fd = sys.stdin.fileno() if sys.stdin.isatty() else None
        self.saved = None
        if self.fd is not None:
            import termios
            import tty

            self.saved = termios.tcgetattr(self.fd)
            tty.setcbreak(self.fd)

    def read(self):
        out = ""
        while self.fd is not None and select.select([self.fd], [], [], 0)[0]:
            chunk = os.read(self.fd, 64).decode(errors="ignore")
            if not chunk:
                break
            out += chunk
        return out.lower()

    def close(self):
        if self.saved is not None:
            import termios

            termios.tcsetattr(self.fd, termios.TCSADRAIN, self.saved)
            self.saved = None


class InteractiveDriver(RoverDriver):
    HELP = "keys (in this terminal): i/k throttle, j/l steer, space stop, c centre steer, m steer mode, u/o ride height"

    def __init__(self, **kw):
        super().__init__(**kw)
        self.keys = TerminalKeys()
        self.pressed = ""

    def Synchronize(self, time):
        self.pressed = self.keys.read()
        for k in self.pressed:
            if k == "i":
                self.SetSpeed(self.speed + self.max_speed * 0.1)
            elif k == "k":
                self.SetSpeed(self.speed - self.max_speed * 0.1)
            elif k == " ":
                self.SetSpeed(0.0)
            elif k == "j":
                self.SetSteering(self.steer + math.radians(5))
            elif k == "l":
                self.SetSteering(self.steer - math.radians(5))
            elif k == "c":
                self.SetSteering(0.0)
            elif k == "m":
                self.SetMode(MODES[(MODES.index(self.mode) + 1) % len(MODES)])
            elif k == "u":
                self.SetLifting(min(0.6, self.ride + 0.05))
            elif k == "o":
                self.SetLifting(max(-0.6, self.ride - 0.05))

    def close(self):
        self.keys.close()


class Example:
    def __init__(self, args):
        self.args = args
        self.step_size = args.step
        self.sim_time = 0.0
        self.frame = 0
        g = 9.81 if args.earth else G_MOON
        self.system = sys_ = chrono.ChSystemNSC()
        sys_.SetCollisionSystemType(chrono.ChCollisionSystem.Type_BULLET)
        sys_.SetGravitationalAcceleration(chrono.ChVector3d(0, 0, -g))
        sys_.SetSolverType(chrono.ChSolver.Type_BARZILAIBORWEIN)
        sys_.GetSolver().AsIterative().SetMaxIterations(150)
        sys_.SetMaxPenetrationRecoverySpeed(0.2)
        chrono.ChCollisionModel.SetDefaultSuggestedEnvelope(0.005)
        chrono.ChCollisionModel.SetDefaultSuggestedMargin(0.002)

        self.mat = chrono.ChContactMaterialData()
        self.mat.mu = args.friction
        self.mat.cr = 0.0
        self.urdf = args.urdf or find_urdf(args.asset)
        self.driver = self.create_driver()
        self.add_terrain()
        meta = json.load(open(self.urdf + ".json"))
        hulls = {n: HULL for n in self.hull_links(meta)}
        pose = chrono.ChFramed(chrono.ChVector3d(0, 0, args.drop), chrono.QuatFromAngleZ(math.radians(args.yaw)))
        self.robot = UrdfRobot(sys_, self.urdf, pose, self.driver.motor_type, self.mat, hulls)
        self.chassis = self.robot.chassis
        self.wheel_override = {}
        self.configure_rover()

        ref = self.chassis.GetFrameRefToAbs()
        self.wheels = {}
        for j in self.robot.role("drive"):
            corner = j.name[: -len("_wheel")] if j.name.endswith("_wheel") else j.name
            p = ref.TransformPointParentToLocal(self.robot.body(j.name).GetPos())
            r = self.robot.collision_radius(j.name, self.robot.axis(j.name)) or 0.3
            self.wheels[corner] = {"x": p.x, "y": p.y, "r": r, "joint": j, "steer": self.robot.joints.get(f"{corner}_steer")}
        self.active = [(next((c for c in self.wheels if j.name.startswith(c + "_")), None), j)
                       for j in self.robot.role("active_suspension")]
        self.springs = [j for j in self.robot.joints.values() if j.actuation == ACT.ActuationType_FORCE and j.role not in ("drive", "active_suspension")
                        and j.drive.get("kind") == "spring"]
        fixed_x = [w["x"] for w in self.wheels.values() if not w["steer"]]
        self.turn_x = sum(fixed_x) / len(fixed_x) if fixed_x else 0.0
        self.all_steer = bool(self.wheels) and all(w["steer"] for w in self.wheels.values())
        self.servo = [j for j in self.robot.joints.values() if j.actuation == ACT.ActuationType_POSITION and j.role != "steer"]
        for name, v in self.initial_pose().items():
            if name in self.robot.joints:
                self.robot.joints[name].target = v
        self.start = self.pos()
        steer = "all-wheel steer" if self.all_steer else ("steered" if any(w["steer"] for w in self.wheels.values()) else "skid steer")
        mass = sum(b.GetMass() for b in sys_.GetBodies() if not b.IsFixed())
        print(f"{os.path.basename(self.urdf)}: {len(sys_.GetBodies())} bodies, {len(sys_.GetLinks())} links, {mass:.0f} kg, "
              f"{len(self.wheels)} driven wheels ({self.driver.motor_type}), {steer}, {len(self.robot.loops)} loop closures, "
              f"servos: {', '.join(j.name for j in self.servo) or 'none'}")
        self.vis = self.create_vis() if args.vis != "none" else None
        if isinstance(self.driver, InteractiveDriver):
            print(InteractiveDriver.HELP)

    def create_driver(self):
        a = self.args
        kw = {"max_speed": a.max_speed}
        if a.driver == "speed":
            return SpeedDriver(speed=a.speed, **kw)
        if a.driver == "dc":
            return DCMotorDriver(speed=a.speed, stall_torque=a.stall_torque, no_load_speed=a.no_load_speed, **kw)
        if a.driver == "demo":
            return ScriptedDriver(self.demo_script(), **kw)
        d = InteractiveDriver(**kw)
        d.SetSpeed(a.speed)
        d.SetSteering(math.radians(a.steer))
        return d

    def demo_script(self):
        v = self.args.max_speed * 0.5
        return [(1.0, "drive", (v, 0.0)), (6.0, "drive", (v, math.radians(20))), (11.0, "mode", "crab"),
                (11.0, "drive", (v, math.radians(30))), (15.0, "mode", "spin"), (15.0, "drive", (v * 0.7, 0.0)),
                (20.0, "mode", "ackermann"), (20.0, "drive", (0.0, 0.0))]

    def initial_pose(self):
        return {}

    def hull_links(self, meta):
        return {"chassis", *(n for n, j in meta["joints"].items() if j["role"] == "drive")}

    def configure_rover(self):
        pass

    def add_terrain(self):
        a = self.args
        self.terrain, self.scm_domain = None, False
        if a.terrain == "rigid":
            self.add_ground_box(0.0, 0.0, a.size, a.size)
            return
        import pychrono.vehicle as veh

        if a.terrain == "scm":
            length, width, cx = a.size, a.size, 0.0
        else:
            length, width, cx = a.scm_length, a.scm_width, a.scm_x
            x0, x1, y0, y1 = cx - length / 2, cx + length / 2, -width / 2, width / 2
            h = a.size / 2
            self.add_ground_box((x0 - h) / 2, 0.0, x0 + h, a.size)
            self.add_ground_box((x1 + h) / 2, 0.0, h - x1, a.size)
            self.add_ground_box(cx, (y0 - h) / 2, length, y0 + h)
            self.add_ground_box(cx, (y1 + h) / 2, length, h - y1)
        self.terrain = veh.SCMTerrain(self.system)
        self.terrain.SetReferenceFrame(chrono.ChCoordsysd(chrono.ChVector3d(cx, 0, 0), chrono.QUNIT))
        self.terrain.SetSoilParameters(a.scm_kphi, a.scm_kc, a.scm_n, a.scm_cohesion, a.scm_phi, a.scm_janosi, 4e7, 3e4)
        self.terrain.Initialize(length, width, a.scm_delta)
        self.terrain.SetPlotType(veh.SCMTerrain.PLOT_SINKAGE, 0, 0.05)
        self.terrain.SetColor(chrono.ChColor(0.55, 0.53, 0.5))
        self.terrain.SetMeshWireframe(False)
        print(f"SCM terrain {length:.1f} x {width:.1f} m at x = {cx:+.1f}, grid {a.scm_delta * 100:.0f} cm"
              + (", rigid ground around it" if a.terrain == "section" else ""))

    def add_ground_box(self, x, y, lx, ly):
        if lx <= 1e-6 or ly <= 1e-6:
            return
        ground = chrono.ChBodyEasyBox(lx, ly, 0.2, 1000, True, True, self.mat.CreateMaterial(self.system.GetContactMethod()))
        ground.SetPos(chrono.ChVector3d(x, y, -0.1))
        ground.SetFixed(True)
        ground.GetVisualShape(0).SetTexture(chrono.GetChronoDataFile("textures/concrete.jpg"), lx / 4, ly / 4)
        ground.GetVisualShape(0).SetColor(chrono.ChColor(0.55, 0.54, 0.52))
        self.system.Add(ground)

    def create_vis(self):
        a = self.args
        p = self.chassis.GetPos()
        eye = p + chrono.ChVector3d(-4.5, -4.5, 2.5)
        if a.vis == "irrlicht":
            import pychrono.irrlicht as irr

            vis = irr.ChVisualSystemIrrlicht()
            vis.AttachSystem(self.system)
            vis.SetCameraVertical(chrono.CameraVerticalDir_Z)
            vis.SetWindowSize(1600, 900)
            vis.SetWindowTitle(self.title())
            vis.Initialize()
            vis.AddSkyBox()
            vis.AddCamera(eye, p)
            vis.AddTypicalLights()
            return vis
        import pychrono.vsg3d as vsg

        vis = vsg.ChVisualSystemVSG()
        vis.AttachSystem(self.system)
        vis.SetCameraVertical(chrono.CameraVerticalDir_Z)
        vis.SetWindowSize(1600, 900)
        vis.SetWindowTitle(self.title())
        vis.AddCamera(eye, p)
        vis.SetBackgroundColor(chrono.ChColor(0.02, 0.02, 0.03))
        vis.SetLightDirection(math.radians(a.sun_az), math.radians(a.sun_el))
        vis.SetLightIntensity(1.2)
        vis.EnableShadows(a.shadows)
        vis.Initialize()
        return vis

    def title(self):
        return f"{os.path.splitext(os.path.basename(self.urdf))[0]} - Chrono"

    def corner_commands(self):
        d = self.driver
        v, steer = d.speed / 3.6, d.steer
        out = {}
        if not any(w["steer"] for w in self.wheels.values()):
            half = max(abs(w["y"]) for w in self.wheels.values())
            yaw = v * math.tan(steer) / max(half, 1e-3) * 1.5
            return {c: (0.0, (v - yaw * w["y"]) / w["r"]) for c, w in self.wheels.items()}
        if d.mode == "crab":
            return {c: (steer if w["steer"] else 0.0, v / w["r"]) for c, w in self.wheels.items()}
        if d.mode == "spin" and self.all_steer:
            r_ref = max(math.hypot(w["x"], w["y"]) for w in self.wheels.values())
            for c, w in self.wheels.items():
                ang, sgn = math.atan2(w["x"], -w["y"]), 1.0
                if ang > math.pi / 2:
                    ang, sgn = ang - math.pi, -1.0
                elif ang < -math.pi / 2:
                    ang, sgn = ang + math.pi, -1.0
                out[c] = (ang, sgn * v * math.hypot(w["x"], w["y"]) / r_ref / w["r"])
            return out
        if abs(steer) < 1e-4:
            return {c: (0.0, v / w["r"]) for c, w in self.wheels.items()}
        span = max(abs(w["x"] - self.turn_x) for w in self.wheels.values())
        radius = span / math.tan(steer)
        for c, w in self.wheels.items():
            dx, dy = w["x"] - self.turn_x, radius - w["y"]
            ang = math.atan2(dx, dy) if radius > 0 else -math.atan2(dx, -dy)
            out[c] = (ang if w["steer"] else 0.0, v * math.hypot(dx, dy) / abs(radius) / w["r"])
        return out

    def write_targets(self):
        d = self.driver
        for c, (ang, omega) in self.corner_commands().items():
            w = self.wheels[c]
            if w["steer"]:
                w["steer"].target = ang
            j = w["joint"]
            omega = self.wheel_override.get(c, omega)
            j.set(omega if d.motor_type == "speed" else d.wheel_torque(omega, j.velocity()))
        for corner, j in self.active:
            k, c = j.drive.get("stiffness", 0.0), j.drive.get("damping", 0.0)
            target = min(max(j.drive.get("target", 0.0) - d.ride + d.lift.get(corner, 0.0), j.lower), j.upper)
            tau = k * (target - j.position()) - c * j.velocity()
            lim = j.drive.get("max_force") or j.effort or abs(tau)
            j.set(max(-lim, min(lim, tau)))
        for j in self.springs:
            tau = j.drive.get("stiffness", 0.0) * (j.drive.get("target", 0.0) - j.position()) - j.drive.get("damping", 0.0) * j.velocity()
            lim = j.drive.get("max_force") or abs(tau)
            j.set(max(-lim, min(lim, tau)))
        self.robot.update_servos(self.step_size)

    def handle_keys(self, keys):
        for key, role in TOGGLES.items():
            if key in keys:
                for j in [j for j in self.servo if j.role == role]:
                    far = j.upper if abs(j.upper) >= abs(j.lower) else j.lower
                    j.target = 0.0 if abs(j.target) > 1e-3 else far

    def add_scm_domain(self):
        if self.args.scm_domain:
            size = chrono.ChVector3d(*self.args.scm_domain)
            centre = chrono.ChVector3d(0, 0, 0)
        else:
            xs = [w["x"] for w in self.wheels.values()] or [0.0]
            ys = [w["y"] for w in self.wheels.values()] or [0.0]
            r = max([w["r"] for w in self.wheels.values()] or [0.3])
            size = chrono.ChVector3d(max(xs) - min(xs) + 2 * r + 0.6, max(ys) - min(ys) + 2 * r + 0.6, 3.0)
            centre = chrono.ChVector3d((max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2, 0.0)
        self.terrain.AddActiveDomain(self.chassis, centre, size)
        self.scm_domain = True
        print(f"SCM active domain {size.x:.2f} x {size.y:.2f} x {size.z:.2f} m following the chassis")

    def update(self):
        pass

    def step(self):
        self.driver.Synchronize(self.sim_time)
        if isinstance(self.driver, InteractiveDriver) and self.driver.pressed:
            self.handle_keys(self.driver.pressed)
        self.update()
        if self.terrain is not None and not self.scm_domain:
            self.add_scm_domain()
        self.write_targets()
        self.system.DoStepDynamics(self.step_size)
        self.sim_time += self.step_size
        self.frame += 1

    def follow_camera(self):
        if not self.args.follow:
            return
        p = self.chassis.GetPos()
        yaw = self.yaw()
        off = chrono.ChVector3d(-5.0 * math.cos(yaw) + 2.5 * math.sin(yaw), -5.0 * math.sin(yaw) - 2.5 * math.cos(yaw), 2.2)
        if self.args.vis == "vsg":
            self.vis.SetCameraPosition(p + off)
            self.vis.SetCameraTarget(p)
        else:
            self.vis.UpdateCamera(p + off, p)

    def render(self):
        self.follow_camera()
        self.vis.BeginScene()
        self.vis.Render()
        self.vis.EndScene()

    def pos(self):
        return chrono.ChVector3d(self.chassis.GetFrameRefToAbs().GetPos())

    def yaw(self):
        q = self.chassis.GetRot()
        return math.atan2(2 * (q.e0 * q.e3 + q.e1 * q.e2), 1 - 2 * (q.e2 * q.e2 + q.e3 * q.e3))

    def ground_speed(self):
        v = self.chassis.GetPosDt()
        return math.hypot(v.x, v.y)

    def status(self):
        d = self.driver
        p = self.pos()
        return (f"t {self.sim_time:6.2f} s  pos ({p.x:+6.2f}, {p.y:+6.2f}, {p.z:+5.2f})  yaw {math.degrees(self.yaw()):+6.1f}  "
                f"v {self.ground_speed() * 3.6:5.2f} km/h  cmd {d.speed:+5.2f} km/h {math.degrees(d.steer):+5.1f} deg {d.mode}")

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
                        self.render()
                self.step()
                if self.vis is not None and not a.fast:
                    timer.Spin(self.step_size)
                if self.frame % round(1.0 / self.step_size) == 0 and (self.vis is None or not isinstance(self.driver, InteractiveDriver)):
                    print(self.status())
        finally:
            self.driver.close()
        wall = wallclock.perf_counter() - t0
        print(f"\nsimulated {self.sim_time:.2f} s in {wall:.1f} s wall (RTF {wall / max(self.sim_time, 1e-9):.2f})")
        if a.test:
            self.test_final()

    def test_final(self):
        low = min(b.GetPos().z for b in self.system.GetBodies() if not b.IsFixed())
        p = self.pos()
        checks = {"all bodies above the ground": low > -0.05, "chassis upright": self.chassis.GetRot().GetAxisZ().z > 0.9,
                  "loop closures hold": self.max_loop_gap() < 0.005}
        for k, ok in checks.items():
            print(f"[{'ok' if ok else 'FAIL'}] {k}")
        print(f"final chassis position ({p.x:.3f}, {p.y:.3f}, {p.z:.3f}), t = {self.sim_time:.1f} s")
        assert all(checks.values()), "rover checks failed"

    def max_loop_gap(self):
        gap = 0.0
        for link in self.robot.loops:
            f1, f2 = link.GetFrame1Abs(), link.GetFrame2Abs()
            d = f1.GetPos() - f2.GetPos()
            if isinstance(link, chrono.ChLinkLockPointLine):
                x = f2.GetRotMat().GetAxisX()
                d = d - x * d.Dot(x)
            gap = max(gap, d.Length())
        return gap

    @staticmethod
    def create_parser():
        parser = argparse.ArgumentParser(description="Drive a lunar rover URDF in Project Chrono.")
        parser.add_argument("--asset", default="ltv_concept", help="Asset id; finds assets/*/*/*/urdf/<id>.urdf.")
        parser.add_argument("--urdf", default=None, help="Explicit path to a rover URDF (with its .urdf.json sidecar).")
        parser.add_argument("--vis", default="vsg", choices=["vsg", "irrlicht", "none"], help="Run-time visualisation.")
        parser.add_argument("--driver", default="interactive", choices=["interactive", "speed", "dc", "demo"],
                            help="interactive (terminal keys), speed (wheel speed motors), dc (DC motor torque curve), demo (script).")
        parser.add_argument("--terrain", default="rigid", choices=["rigid", "scm", "section"],
                            help="rigid ground, scm (whole patch deformable) or section (an SCM strip set into rigid ground).")
        parser.add_argument("--speed", type=float, default=0.0, help="Initial / cruise speed [km/h].")
        parser.add_argument("--steer", type=float, default=0.0, help="Initial steer angle [deg].")
        parser.add_argument("--max-speed", type=float, default=10.0, help="Throttle limit [km/h].")
        parser.add_argument("--stall-torque", type=float, default=54.5, help="DC driver stall torque per wheel [N m].")
        parser.add_argument("--no-load-speed", type=float, default=1.2, help="DC driver no-load wheel speed [rad/s].")
        parser.add_argument("--drop", type=float, default=0.02, help="Initial height of the URDF root above the ground [m].")
        parser.add_argument("--yaw", type=float, default=0.0, help="Initial heading [deg].")
        parser.add_argument("--friction", type=float, default=0.8, help="Wheel-ground friction coefficient.")
        parser.add_argument("--size", type=float, default=40.0, help="Terrain patch size [m].")
        parser.add_argument("--scm-delta", type=float, default=0.04, help="SCM grid spacing [m].")
        parser.add_argument("--scm-length", type=float, default=6.0, help="SCM section length along x [m] (--terrain section).")
        parser.add_argument("--scm-width", type=float, default=4.0, help="SCM section width along y [m] (--terrain section).")
        parser.add_argument("--scm-x", type=float, default=4.0, help="SCM section centre x [m] (--terrain section).")
        parser.add_argument("--scm-domain", type=float, nargs=3, default=None, metavar=("LX", "LY", "LZ"),
                            help="Active domain box around the chassis [m]; defaults to the rover footprint plus a margin.")
        parser.add_argument("--scm-kphi", type=float, default=0.82e6, help="SCM Bekker Kphi [Pa/m^n] (lunar regolith).")
        parser.add_argument("--scm-kc", type=float, default=0.14e4, help="SCM Bekker Kc [Pa/m^(n-1)].")
        parser.add_argument("--scm-n", type=float, default=1.0, help="SCM Bekker exponent n.")
        parser.add_argument("--scm-cohesion", type=float, default=170.0, help="SCM Mohr cohesion [Pa].")
        parser.add_argument("--scm-phi", type=float, default=35.0, help="SCM Mohr friction angle [deg].")
        parser.add_argument("--scm-janosi", type=float, default=0.018, help="SCM Janosi shear modulus [m].")
        parser.add_argument("--step", type=float, default=1e-3, help="Integration step [s].")
        parser.add_argument("--time", type=float, default=0.0, help="Stop after this many simulated seconds (0 = run until closed).")
        parser.add_argument("--earth", action="store_true", help="Earth gravity.")
        parser.add_argument("--follow", action="store_true", help="Chase camera.")
        parser.add_argument("--shadows", action="store_true", help="VSG shadows.")
        parser.add_argument("--sun-az", type=float, default=60.0, help="Sun azimuth [deg].")
        parser.add_argument("--sun-el", type=float, default=12.0, help="Sun elevation [deg].")
        parser.add_argument("--fast", action="store_true", help="Run as fast as possible instead of real time.")
        parser.add_argument("--test", action="store_true", help="Run checks at the end.")
        return parser


if __name__ == "__main__":
    Example(Example.create_parser().parse_args()).run()
