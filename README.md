[![Latest release](https://img.shields.io/github/v/release/alexmaietta/lunar-surface-mobility-assets?label=release)](https://github.com/alexmaietta/lunar-surface-mobility-assets/releases/latest)
[![Code: Apache-2.0](https://img.shields.io/badge/code-Apache--2.0-blue.svg)](LICENSE)
[![Assets: CC BY 4.0](https://img.shields.io/badge/assets-CC%20BY%204.0-lightgrey.svg)](LICENSE-ASSETS)
![USD](https://img.shields.io/badge/format-OpenUSD-6a5acd.svg)
![Blender](https://img.shields.io/badge/format-Blender-e87d0d.svg?logo=blender&logoColor=white)
![glTF](https://img.shields.io/badge/format-glTF-87c540.svg)
![OBJ](https://img.shields.io/badge/format-OBJ-555555.svg)
![Isaac Sim](https://img.shields.io/badge/Isaac%20Sim-robot%20layout-76b900.svg?logo=nvidia&logoColor=white)
![Newton](https://img.shields.io/badge/Newton-1.6-76b900.svg)

# Lunar Surface Mobility Assets

![Every asset in this repo on the lunar surface, Cycles render](docs/images/hero.jpg)

These are simulation-ready models of lunar landers, rovers and their friends. Each one is built procedurally in Blender from public references and gets generated, high-resolution, tileable PBR textures. It ships as an Isaac Sim / SimReady-style **USD** asset with physics, joints, colliders and named sites for engines, RCS thrusters, sensors and antennas. The rovers add drive, steering and suspension joints, working hatches, stairs and arms, and real `UsdLux` lights. Each asset also comes in various formats, such as **glTF**, **OBJ** and **Blender**.

**[Explore every model in 3D](https://alexmaietta.github.io/lunar-surface-mobility-assets/)** The interactive viewer puts all of the landers and rovers on the lunar surface at true scale, next to a 1.8 m human. Orbit around them, click any vehicle for its specs, and drive its moving parts, such as engine gimbals, antennas, arms, hatches, stairs, steering and wheels. It runs in the browser with nothing to install (see [Web viewer](#web-viewer)).

| Vendor | Vehicle | Asset | Status |
|---|---|---|---|
| Blue Origin | [Blue Moon MK1](assets/blue_origin/mk1/lander) lander | `mk1` | v0.1: photo-matched, packaged, Newton-tested |
| Blue Origin | [Blue Moon MK1](assets/blue_origin/mk1/offloader) payload offloader | `mk1_offloader` | v0.1: packaged, Newton-tested on `mk1` |
| Grumman / NASA | [Apollo Lunar Module](assets/grumman/apollo_lm/lander) (J-mission) | `apollo_lm` | v0.1: drawing-matched, packaged, Newton-tested |
| Intuitive Machines | [Nova-C](assets/intuitive_machines/nova_c/lander) (IM-1 / IM-2) | `nova_c` | v0.1: photo-matched, packaged, Newton-tested |
| Firefly Aerospace | [Blue Ghost](assets/firefly/blue_ghost/lander) (Mission 1) | `blue_ghost` | v0.1: photo-matched, packaged, Newton-tested |
| Astrobotic | [Peregrine](assets/astrobotic/peregrine/lander) (Mission One) | `peregrine` | v0.1: photo-matched, packaged, Newton-tested |
| Toyota / JAXA | [Lunar Cruiser](assets/toyota_jaxa/lunar_cruiser/rover) pressurised rover (2025 design) | `lunar_cruiser` | v0.1: spec-matched, packaged, Newton-tested |
| NASA | [Space Exploration Vehicle](assets/nasa/sev/rover) (SEV / LER, 2010) | `sev` | v0.1: photo-matched, packaged, Newton-tested |
| NASA | [VIPER](assets/nasa/viper/rover) | `viper` | v0.1: photo-matched, packaged, Newton-tested |
| NASA / JPL | [CADRE](assets/nasa_jpl/cadre/rover) rover (IM-3) | `cadre` | v0.1: photo-matched, packaged, Newton-tested |
| Astrolab | [FLEX](assets/astrolab/flex/rover) prototype | `flex` | v0.1: photo-matched, packaged, Newton-tested |
| Astrolab | [CLV-1](assets/astrolab/clv1/rover) LTV (NASA task order 2026) | `clv1` | v0.1: render-matched, packaged, Newton-tested |
| Astrolab | [FLIP](assets/astrolab/flip/rover) (Griffin-1) | `flip` | v0.1: render-matched, packaged, Newton-tested |
| Lunar Outpost | [Pegasus](assets/lunar_outpost/pegasus/rover) LTV (NASA task order 2026) | `pegasus` | v0.1: photo-matched, packaged, Newton-tested |
| Lunar Outpost | [Eagle](assets/lunar_outpost/eagle/rover) LTV bid | `eagle` | v0.1: photo-matched, packaged, Newton-tested |
| Lunar Outpost | [MAPP](assets/lunar_outpost/mapp/rover) (IM-2) | `mapp` | v0.1: photo-matched, packaged, Newton-tested |
| Intuitive Machines | [Moon RACER](assets/intuitive_machines/moon_racer/rover) LTV bid | `moon_racer` | v0.1: photo-matched, packaged, Newton-tested |
| Concept | [Lunar Terrain Vehicle](assets/concepts/ltv/rover), crewed or uncrewed | `ltv_concept` | v0.1: concept, packaged, Newton-tested |
| Concept | [Pressurised rover](assets/concepts/pressurized/rover) | `pr_concept` | v0.1: concept, packaged, Newton-tested |
| Blue Origin | Blue Moon MK2 crewed lander | `mk2` | planned |

All assets share one frame and are built to scale (Z up, metres, origin on the ground under the centerline), so they can be placed side by side:

| Asset | Height | Footpad span | Legs | Launch / touchdown / dry mass | Main propulsion |
|---|---|---|---|---|---|
| `mk1` | 8.05 m | 6.1 m | 4 | 21,350 / 7,900 / 7,000 kg | 1 × BE-7, 44.5 kN, LOX/LH2, gimballed |
| `apollo_lm` | 7.04 m (drawing), model 6.92 m | 8.51 m pad centres (31 ft over pads) | 4 | 16,400 / 8,000 / 4,900 kg | DPS 43.9 kN, throttled 10–65 %, gimballed; APS 15.6 kN fixed |
| `nova_c` | 4.30 m (official), model 4.23 m | 4.6 m | 6 | 1,908 / 860 / 775 kg | 1 × VR900, 3.1 kN, LOX/LCH4, gimballed |
| `blue_ghost` | 2.0 m deck, 2.77 m with stowed antenna | 3.7 m pad centres (diagonal) | 4 | 1,517 / 560 / 469 kg | 1 × LEROS 4-ET, 1.31 kN, MMH/MON-3, fixed |
| `peregrine` | 1.90 m | 2.47 m face-on, 3.5 m diagonal | 4 | 1,283 / 580 / 503 kg | 5 × 667 N, MMH/MON-25, pulsed |

The rovers use the same frame, with the origin on the ground under the chassis centre at nominal ride height:

| Asset | L × W × H | Mass | Wheels | Suspension and steering | Mechanisms |
|---|---|---|---|---|---|
| `lunar_cruiser` | 7.96 × 4.86 × 4.98 m (with folded stair and dish) | 18,000 kg loaded, 15,000 launch | 6 × 1.18 m metal slat | double wishbone with coilover struts; front axle steers | hinged airlock hatch with hand-wheel latch and 4 sliding latch bolts, two-flight folding stair with fold-flat railings, swing-out solar wings (4 × 10 m blankets), rear arm, Ka-band dish |
| `pr_concept` | 7.55 × 3.52 × 4.30 m | 9,000 kg (7,800 dry, 10,000 loaded) | 6 × 1.10 m | active double wishbone; every wheel steers (crab) | suitport hatches or airlock door, IDSS-style docking hatch, roof solar wings, 2.6 m arm |
| `sev` | 5.16 × 4.12 × 3.57 m | 3,000 kg (4,000 loaded) | 12 × 0.80 m on 6 columns | active prismatic legs; 360° steering columns (crab, turn in place) | suitport hatches, side docking hatch |
| `ltv_concept` | 3.88 × 2.76 × 2.35 m | 1,100 kg (1,900 crewed, 2,700 uncrewed) | 4 × 0.90 m airless | active double wishbone; all-wheel steer | 5-axis arm, tilting solar array, pan-tilt mast, dish |
| `flex` | 3.41 × 2.48 × 3.92 m | 500 kg prototype (1,500 with cargo) | 4 × 0.67 m airless | active wheel-on-limb legs; all-wheel and crab steer | 6-axis 2.4 m arm, hinged 3 m² solar array |
| `clv1` | 3.98 × 2.34 × 2.65 m | 950 kg (1,490 crewed) | 4 × 0.93 m Venturi | active limbs; all-wheel steer | pan-tilt mast, dish |
| `pegasus` | 3.62 × 2.56 (3.04 with wings) × 2.90 m | 1,000 kg (1,540 crewed) | 4 × 0.82 m spring mesh | double wishbone; all-wheel steer | hinged solar wings, dish |
| `eagle` | 4.00 × 2.48 × 2.58 m | 1,600 kg (2,140 crewed) | 4 × 1.0 m | double wishbone; all-wheel steer | tilting solar panel, arm |
| `moon_racer` | 4.46 × 2.52 × 2.74 m | 1,100 kg (1,650 crewed, 2,050 loaded) | 4 × 0.80 m airless | double wishbone with coilovers; front steer | arm, dish |
| `flip` | 2.33 × 1.91 × 2.30 m | 480 kg | 4 × 0.93 m Venturi | active swing arms; all-wheel steer | – |
| `viper` | 1.74 × 1.72 × 2.53 m | 447 kg roving, 490 launch | 4 × 0.50 m grousered | active swing arms (wheel walking, 7–43 cm clearance); ±50° steer | TRIDENT drill (1.1 m prismatic), pan-tilt mast, dish |
| `mapp` | 0.45 × 0.39 × 0.44 m | 10 kg | 4 × 0.12 m paddle | rockers; skid steer | – |
| `cadre` | 0.56 × 0.81 × 0.35 m (wings open) | 8.6 kg | 4 × 0.16 m grousered | rigid; skid steer | hinged solar wings, flip-up camera covers |

## Quick Start

Each asset is released as `<asset>-usd.zip`, `<asset>-gltf.zip`, `<asset>-obj.zip` and `<asset>-blend.zip` on the [latest release](https://github.com/alexmaietta/lunar-surface-mobility-assets/releases/latest). For small downloads, `<asset>-simple-usd.zip`, `<asset>-simple-gltf.zip` and `<asset>-simple-obj.zip` hold a single simplified mesh of a few hundred kB (see [Simple versions](#simple-versions)). To pin a version, use `download/v0.1.0` instead of `latest/download`; each release includes `SHA256SUMS`.

```sh
curl -LO https://github.com/alexmaietta/lunar-surface-mobility-assets/releases/latest/download/mk1-usd.zip
unzip mk1-usd.zip # -> mk1/mk1.usda
curl -LO https://github.com/alexmaietta/lunar-surface-mobility-assets/releases/latest/download/mk1-simple-gltf.zip
unzip mk1-simple-gltf.zip # -> mk1_simple/mk1_simple.glb
```

Or clone the repo. The same assets are in `assets/`, stored with Git LFS (set `GIT_LFS_SKIP_SMUDGE=1` to skip them):

```sh
git clone git@github.com:alexmaietta/lunar-surface-mobility-assets.git && cd lunar-surface-mobility-assets && git lfs pull
```

To contribute, enable the repo hooks once per clone. They run Git LFS and `scripts/check_large_files.py`, which blocks a commit if any file over 4 MB would go into git instead of LFS (the `size-guard` workflow runs the same check on every push):

```sh
git config core.hooksPath .githooks && git lfs install --local
```

Open `assets/blue_origin/mk1/lander/usd/mk1.usda` in Isaac Sim or another Omniverse app and switch variants in the Variant Presenter, or select one in code:

```python
from pxr import Usd
stage = Usd.Stage.Open("assets/blue_origin/mk1/lander/usd/mk1.usda")
root = stage.GetPrimAtPath("/mk1")
root.GetVariantSet("Offloader").SetVariantSelection("crane")
root.GetVariantSet("Propellant").SetVariantSelection("launch")
```

Rovers work the same way:

```python
stage = Usd.Stage.Open("assets/toyota_jaxa/lunar_cruiser/rover/usd/lunar_cruiser.usda")
root = stage.GetPrimAtPath("/lunar_cruiser")
root.GetVariantSet("Solar").SetVariantSelection("deployed")   # wing boxes swung out, 4 x 10 m blankets raised
root.GetVariantSet("Lights").SetVariantSelection("on")
```

## Gallery

Cycles renders on the lunar surface.

| | |
|---|---|
| ![MK1 front three-quarter](docs/images/blue_origin/mk1/lander/front_three_quarter.jpg) | ![MK1 side](docs/images/blue_origin/mk1/lander/side.jpg) |
| ![MK1 engine and legs](docs/images/blue_origin/mk1/lander/low_engine.jpg) | ![MK1 deck](docs/images/blue_origin/mk1/lander/top_deck.jpg) |
| ![MK1 with the offloader](docs/images/blue_origin/mk1/lander/crane/front_three_quarter.jpg) | ![MK1 offloader](docs/images/blue_origin/mk1/offloader/lunar.jpg) |
| ![Apollo LM front three-quarter](docs/images/grumman/apollo_lm/lander/front_three_quarter.jpg) | ![Apollo LM descent engine and legs](docs/images/grumman/apollo_lm/lander/low_engine.jpg) |
| ![Nova-C front three-quarter](docs/images/intuitive_machines/nova_c/lander/front_three_quarter.jpg) | ![Nova-C engine and legs](docs/images/intuitive_machines/nova_c/lander/low_engine.jpg) |
| ![Blue Ghost front three-quarter](docs/images/firefly/blue_ghost/lander/front_three_quarter.jpg) | ![Blue Ghost side](docs/images/firefly/blue_ghost/lander/side.jpg) |
| ![Peregrine front three-quarter](docs/images/astrobotic/peregrine/lander/front_three_quarter.jpg) | ![Peregrine side](docs/images/astrobotic/peregrine/lander/side.jpg) |

### Rovers

The JAXA / Toyota Lunar Cruiser running its full sequence in Newton, played back in Blender ([MP4](docs/videos/lunar_cruiser_sequence.mp4)). It drives, swings its solar wings out to face a low polar sun while the dish tracks Earth, switches its lights on, unfolds the stair, turns the hand wheel to retract the latch bolts, opens the airlock and reaches with the arm:

![Lunar Cruiser sequence](docs/images/toyota_jaxa/lunar_cruiser/rover/sequence.gif)

| | | |
|---|---|---|
| ![Lunar Cruiser front three-quarter](docs/images/toyota_jaxa/lunar_cruiser/rover/front_three_quarter.jpg) | ![Lunar Cruiser rear patio, stair deployed](docs/images/toyota_jaxa/lunar_cruiser/rover/rear_patio.jpg) | ![Lunar Cruiser airlock open, latch bolts retracted](docs/images/toyota_jaxa/lunar_cruiser/rover/airlock_open.jpg) |
| ![Lunar Cruiser solar wings deployed toward a low sun](docs/images/toyota_jaxa/lunar_cruiser/rover/solar_deployed.jpg) | ![Lunar Cruiser rear patio at night under its own lights](docs/images/toyota_jaxa/lunar_cruiser/rover/rear_patio_night.jpg) | ![Lunar Cruiser wheels and sponson](docs/images/toyota_jaxa/lunar_cruiser/rover/wheel.jpg) |

Each rover from the front, the rear and at night under its own lights:

| | | |
|---|---|---|
| ![Pressurised rover concept front three-quarter](docs/images/concepts/pressurized/rover/front_three_quarter.jpg) | ![Pressurised rover concept rear three-quarter](docs/images/concepts/pressurized/rover/rear_three_quarter.jpg) | ![Pressurised rover concept at night](docs/images/concepts/pressurized/rover/night.jpg) |
| ![NASA SEV front three-quarter](docs/images/nasa/sev/rover/front_three_quarter.jpg) | ![NASA SEV rear three-quarter](docs/images/nasa/sev/rover/rear_three_quarter.jpg) | ![NASA SEV at night](docs/images/nasa/sev/rover/night.jpg) |
| ![LTV concept front three-quarter](docs/images/concepts/ltv/rover/front_three_quarter.jpg) | ![LTV concept rear three-quarter](docs/images/concepts/ltv/rover/rear_three_quarter.jpg) | ![LTV concept at night](docs/images/concepts/ltv/rover/night.jpg) |
| ![Astrolab FLEX front three-quarter](docs/images/astrolab/flex/rover/front_three_quarter.jpg) | ![Astrolab FLEX rear three-quarter](docs/images/astrolab/flex/rover/rear_three_quarter.jpg) | ![Astrolab FLEX at night](docs/images/astrolab/flex/rover/night.jpg) |
| ![Astrolab CLV-1 front three-quarter](docs/images/astrolab/clv1/rover/front_three_quarter.jpg) | ![Astrolab CLV-1 rear three-quarter](docs/images/astrolab/clv1/rover/rear_three_quarter.jpg) | ![Astrolab CLV-1 at night](docs/images/astrolab/clv1/rover/night.jpg) |
| ![Lunar Outpost Pegasus front three-quarter](docs/images/lunar_outpost/pegasus/rover/front_three_quarter.jpg) | ![Lunar Outpost Pegasus rear three-quarter](docs/images/lunar_outpost/pegasus/rover/rear_three_quarter.jpg) | ![Lunar Outpost Pegasus at night](docs/images/lunar_outpost/pegasus/rover/night.jpg) |
| ![Lunar Outpost Eagle front three-quarter](docs/images/lunar_outpost/eagle/rover/front_three_quarter.jpg) | ![Lunar Outpost Eagle rear three-quarter](docs/images/lunar_outpost/eagle/rover/rear_three_quarter.jpg) | ![Lunar Outpost Eagle at night](docs/images/lunar_outpost/eagle/rover/night.jpg) |
| ![Moon RACER front three-quarter](docs/images/intuitive_machines/moon_racer/rover/front_three_quarter.jpg) | ![Moon RACER rear three-quarter](docs/images/intuitive_machines/moon_racer/rover/rear_three_quarter.jpg) | ![Moon RACER at night](docs/images/intuitive_machines/moon_racer/rover/night.jpg) |
| ![Astrolab FLIP front three-quarter](docs/images/astrolab/flip/rover/front_three_quarter.jpg) | ![Astrolab FLIP rear three-quarter](docs/images/astrolab/flip/rover/rear_three_quarter.jpg) | ![Astrolab FLIP at night](docs/images/astrolab/flip/rover/night.jpg) |
| ![NASA VIPER front three-quarter](docs/images/nasa/viper/rover/front_three_quarter.jpg) | ![NASA VIPER rear three-quarter](docs/images/nasa/viper/rover/rear_three_quarter.jpg) | ![NASA VIPER at night](docs/images/nasa/viper/rover/night.jpg) |
| ![Lunar Outpost MAPP front three-quarter](docs/images/lunar_outpost/mapp/rover/front_three_quarter.jpg) | ![Lunar Outpost MAPP rear three-quarter](docs/images/lunar_outpost/mapp/rover/rear_three_quarter.jpg) | ![Lunar Outpost MAPP at night](docs/images/lunar_outpost/mapp/rover/night.jpg) |
| ![NASA JPL CADRE front three-quarter](docs/images/nasa_jpl/cadre/rover/front_three_quarter.jpg) | ![NASA JPL CADRE rear three-quarter](docs/images/nasa_jpl/cadre/rover/rear_three_quarter.jpg) | ![NASA JPL CADRE at night](docs/images/nasa_jpl/cadre/rover/night.jpg) |

## Web viewer

`web/` is a static, interactive 3D viewer of every asset, to scale on the lunar surface. It needs no build step and has no CDN calls: three.js r170 and lil-gui are vendored under `web/vendor/three/` (MIT), and it runs from any static file server, offline included.

- **Fast first load.** It loads the simple version of every asset (9 MB for all of them) in the same line-up as the hero render, with a 1.8 m human for scale.
- **Detailed models.** Once the previews are up, every web-optimised model loads in the background, smallest first, and replaces its preview (67 MB in total; 0.8–5.9 MB each: the full glTF with textures resized to 1024 px and re-encoded as WebP via `EXT_texture_webp`). Clicking a vehicle, choosing it in the panel, or opening `#<asset id>` moves it to the front of the queue and flies the camera to it. Add `?lite` to the URL to load detailed models only on demand.
- **Specs.** Height, footprint, mass states, main engines, thruster counts, joints, plus links to the source files and release downloads.
- **Moving parts.** A slider for every controllable joint, grouped by role: engine gimbals, steering, antennas, cameras, robotic arms, cranes, hatches, latches, stairs, solar arrays and deployables. Wheels have a spin control, and Animate sweeps every joint through its range. Joint axes and limits come from the USD physics layer. Passive joints (landing gear, suspension and loop-closed linkages) are left to simulation.
- **Attachments.** These can be toggled per host, for example the MK1 offloader crane.

Build the models and serve the site locally:

```bash
./pipeline.sh web # assets/ -> web/models/ (preview.glb, full.glb, manifest.json per asset; git-ignored)
./pipeline.sh serve # http://localhost:8000 (PORT=8080 to change)
```

`scripts/web_export.py` reads only `assets/` and `configs/`, so it runs without Blender or `build/`. GitHub Pages can't serve LFS files, so the site is published from releases. The [release workflow](.github/workflows/release.yml) builds `web-models.zip` and attaches it to the release, then starts the [pages workflow](.github/workflows/pages.yml), which unpacks it next to `web/` and deploys. Run the pages workflow by hand (Actions → pages → Run workflow, optionally with a tag) to redeploy. Before the first deploy, set the repository's Pages source to GitHub Actions in Settings → Pages.

## Capabilities

- **Articulation.** The MK1 lander has 11 links and 10 joints, with the offloader attached 15 and 14:
  - BE-7 2-axis gimbal (±6°, position servos)
  - four landing-leg pistons (0.30 m stroke, spring-damper)
  - two solar-array hinges
  - high-gain antenna azimuth and elevation
  - offloader slew, luff and hoist (0–9 m)

  The other landers use the same joint roles: `apollo_lm` has a ±6° DPS gimbal, four crush-strut legs (see [Apollo LM landing gear](#apollo-lm-landing-gear)), the steerable S-band dish and the rendezvous radar (shaft and trunnion); `nova_c` a ±5° VR900 gimbal and six crush-core legs; `blue_ghost` four crush-core legs and a 2-axis X-band panel; `peregrine` four legs.
- **Rover articulation.** Every rover is one articulation rooted at the chassis:
  - Each wheel is a velocity-driven drive joint (`joint:role` `drive`).
  - Steerable wheels and steering columns are position servos (`steer`).
  - The suspension is a real mechanism:
    - **Double wishbones:** the upper arm closes the four-bar with an excluded loop joint, and a coilover strut follows as a cylinder and rod pair closed by a ball joint.
    - **Trailing or swing arms.**
    - **Rockers.**
    - **Prismatic legs.**
  - Passive suspension springs are tuned to each rover's mass for about 7° of static sag. Active suspension (`active_suspension`) is a stiff position servo that sets ride height.
  - Hatches, latches, stairs, railings, solar wings, masts, dishes, drills and arms are position servos with their own roles (`hatch`, `latch`, `stair`, `railing`, `solar`, `camera`, `antenna`, `arm`). That's 46–71 joints on the crewed rovers.
- **Lights.** Every lamp is a site with a `UsdLux.DiskLight` just in front of its lens, with radius, intensity, colour temperature and a 60° cone. The lens also has an emissive material. The `Lights` variant switches them all off. On the Lunar Cruiser the stair-tread LED lights ride on the stair links, so they fold with it.
- **Thrusters.** Every engine and RCS nozzle is a site at the nozzle exit plane, with +Z along the exhaust flow and its thrust, Isp, mass flow, exit radius and propellant as attributes. The same data is in `thrusters.json` for plume tools. The main-engine site rides on the gimbal links, so the plume follows the gimbal.
- **Other sites.** Footpad contacts, touchdown sensors, star trackers, IMU, antennas, solar-array normals, payload interfaces, lift points and the offloader's cable endpoints.
- **Sensors.** SCALPSS plume cameras, navigation and surface cameras as `UsdGeom.Camera` prims on the body.
- **Colliders.** Convex hulls of at most 200 vertices, authored with `newton:maxHullVertices` and `physxConvexHullCollision:hullVertexLimit` set to 255 so neither engine re-simplifies them (PhysX defaults to 64, which can drop a footpad's bottom ring).
- **Mass states.** `Propellant` variant: launch, touchdown (default) and dry, each with its own mass, centre of mass and inertia. Rovers use a `Payload` variant instead (e.g. empty, crewed, uncrewed cargo), with the chassis mass set so the whole vehicle matches each state.
- **Materials.** Tileable PBR texture sets (base colour, roughness, metallic, normal), sized in real-world metres: 4096 px crinkled MLI, painted honeycomb panels, brushed and perforated aluminium (opacity cut-outs), titanium, a heat-tinted regen nozzle, OSR tiles, solar cells and beta cloth.
- **Formats:**

  | Format | Path | Notes |
  |---|---|---|
  | USD | `usd/<id>.usda` | Primary asset. Newton, Isaac Sim / PhysX and MuJoCo schemas, all variants |
  | glTF | `gltf/<id>.glb` | Y-up, textures embedded, one node per link so moving parts can be posed |
  | OBJ | `obj/<id>.obj` + `.mtl` + textures | Y-up, single rest-pose mesh |
  | Blender | `blender/<id>.blend` | Source model with all textures packed |
  | Simple USD | `simple/usd/<id>_simple.usd` | One decimated mesh, flat materials, one rigid body with mass, inertia and per-link convex-hull colliders |
  | Simple glTF / OBJ | `simple/gltf/<id>_simple.glb`, `simple/obj/<id>_simple.obj` | The same mesh, Y-up, no textures |

  Paths are inside each asset folder, `assets/<vendor>/<family>/<name>/`, which also holds that asset's `LICENSE` and `NOTICE`. glTF and OBJ carry the default configuration only (no variants, physics or sites); texture tiling is baked into their UVs.

### USD variants

| Variant set | Options (**default**) |
|---|---|
| `Articulation` | **articulated**, rigid (one rigid body: joints and child bodies removed, child colliders join the root body) |
| `Propellant` | launch, **touchdown**, dry |
| `Offloader` (`mk1`) | **none**, crane (bundled `mk1_offloader`, fixed to the deck mount) |
| `Payload` (rovers) | per rover, e.g. **unloaded**, crewed, uncrewed (`ltv_concept`); **loaded**, launch (`lunar_cruiser`) |
| `Crew` (LTVs) | **crewed** (seats or standing stations, console, hand-holds), cargo or uncrewed (pallet and boxes instead) |
| `Solar` (`lunar_cruiser`, `pr_concept`, `flex`, `cadre`) | **stowed**, deployed (also drives the wing joints to their deployed angles; on `cadre` the default is deployed) |
| `Ports` (`pr_concept`) | **suitports**, airlock |
| `SuitportCover` (`sev`), `Antennas` (`mapp`) | the 2010 inflatable suitport cover; the field-test whip antennas |
| `Lights` (rovers) | **on**, off |
| `LandingGear` (`apollo_lm`) | **spring** (linear spring-damper primaries, secondaries locked), crush (honeycomb crush stages, see below) |
| `Fidelity` | **full**, simple (decimated meshes, flat PBR colours), proxy (one box per part) |
| `Physics` | none, physics (UsdPhysics + Newton), **physx**, mujoco |

The sets are listed strongest first: `Articulation` and `Propellant` override what `Physics` authors. `Articulation` and `Fidelity` combine freely; `rigid` + `simple` is the lightest full-asset setup for crowds of vehicles or far-field rendering.

### Simple versions

Every asset also ships a standalone simple version, built from the same model, for small downloads and scenes with many vehicles. On MK1 it's 7,950 triangles instead of 44,404 and about 0.4 MB instead of 84 MB:

| | Full asset | Simple version |
|---|---|---|
| Geometry | every part, 4096 px PBR textures | one mesh decimated to a triangle budget (`SIMPLE_TRIS`, default 8,000), flat colour, roughness and metallic per material |
| Physics | articulated, per-link colliders, joints and drives | one rigid body: mass, centre of mass and inertia of the default mass state, one convex hull per original link |
| Sites, cameras, variants | yes | no |
| Formats | USD, glTF, OBJ, Blender | USD, glTF, OBJ |

## USD asset structure

The layout follows the Isaac Sim robot asset convention. Inside `usd/`:

| Path | Contents |
|---|---|
| `<id>.usda` | Interface layer: variant sets, `SimReady_Metadata`, `IsaacRobotAPI` |
| `thrusters.json` | Every thruster: prim path, exit centre, flow direction, thrust, Isp, mass flow, exit radius |
| `.thumbs/256x256/<id>.usda.png` | Thumbnail |
| `payloads/base.usda` | Link tree under `/<id>/Geometry`: instanceable visuals, convex-hull colliders, sites, cameras |
| `payloads/robot.usda` | `IsaacRobotAPI`, `IsaacLinkAPI`, `IsaacJointAPI`, `IsaacSiteAPI` |
| `payloads/geometries.usd` | All meshes (binary crate) |
| `payloads/instances.usda` | Instanceable prototypes with visual and physics materials |
| `payloads/materials.usda` | `UsdPreviewSurface` materials; textures in `payloads/Textures/` |
| `payloads/physics_materials.usda` | Friction and restitution per physics material |
| `payloads/Physics/` | `physics.usda`, `physx.usda`, `mujoco.usda` |
| `payloads/Articulation/`, `Fidelity/`, `Propellant/` | One layer per variant option |
| `payloads/<attachment set>/`, `payloads/attachments/<dep>/` | Attachment variants and the bundled attachment packages |

Conventions:
- Z up, metres, kilograms.
- The origin is on the ground under the centreline, with the legs at nominal stroke, so placing an asset at `(x, y, 0)` stands it on the surface.
- Rigid parts are merged per link and material (`<link>__<material>`); only articulated parts are separate links.
- Attachments are assets in their own right. A host lists them in its config, and the packager adds an optional variant set, off by default, that bundles a copy of the attachment, mounts it at a site and joins it to the host's articulation with a fixed joint.

## Validation

| Validator | Result |
|---|---|
| `nvidia_usd_validate` (usd-validation-nvidia 1.22) | 0 errors and 0 failures on `mk1`, `mk1_offloader`, `apollo_lm`, `nova_c`, `blue_ghost` and `peregrine`, with the mesh-weld and indexed-primvar checks off; only non-manifold and zero-area-face warnings remain |
| Newton 1.6 (`SolverMuJoCo`) | `mk1` settles level on all four legs in lunar gravity, tracks the gimbal and antenna servos and lifts off under BE-7 thrust; with `Offloader = crane` (15 bodies) it also tracks slew, luff and hoist targets. `apollo_lm`, `nova_c`, `blue_ghost` and `peregrine` pass every check that applies to them. All 13 rovers settle level on every wheel, track every servo (steering, active suspension, hatches, latches, stairs, railings, wings, arms, masts) and drive; the 18 t Lunar Cruiser also passes its scripted showcase |

`scripts/sim_newton.py` works on any asset. It reads each joint's `joint:role` and `joint:driveKind` from the USD and runs the checks that apply, exiting non-zero if any fails:

| Check | Runs on | Pass condition |
|---|---|---|
| `settle` | every asset | dropped 0.5 m in lunar gravity, comes to rest under 2° tilt; reports passive joint travel (landing gear, suspension) |
| `servo` | position-driven joints (gimbals, antennas, cranes, steering, hatches) | reaches a mid-range target within 1° or 5 cm |
| `drive` | velocity-driven joints (wheels) | travels more than 0.1 m without tipping past 15° |
| `thrust` | `main` thrusters in `thrusters.json` | thrust-to-weight above 1, and 1.05 × weight gives the expected acceleration |
| `touchdown` | assets with prismatic landing-gear joints | reset just above the surface at `--td-vz` sink rate and `--td-vh` drift (default 1.0 and 0.3 m/s), lands below 10° tilt, comes to rest and no crush stage bottoms out; reports peak and final stroke per strut, summing in-series stages, and the minimum main-engine exit clearance |

`--slope <deg>` tilts gravity about +Y, which is equivalent to landing on a slope, and `--mu` sets surface friction. The touchdown check is the lander counterpart to the rovers' `drive` check.

### Apollo LM landing gear

The `apollo_lm` legs are the real mechanism, not a single sprung piston. Each leg has a primary strut, ball-jointed to the descent-stage outrigger, whose inner cylinder carries the footpad on a ball joint (30° cone). Two telescoping secondary struts run from the deployment truss to a ball joint on the primary's outer cylinder; they close the loop as `physics:excludeFromArticulation` joints, which Newton and MuJoCo turn into equality constraints. That is 12 bodies and 2 loop closures per leg.

Every honeycomb stage is its own prismatic joint, in series, with a one-sided limit and joint friction equal to its crush load. A stage does not move until its load is exceeded, then strokes at that load and stays crushed, so the weakest stage crushes first. This is the rigid-plastic load/stroke curve of NASA TN D-6850 (figs. 7 and 9):

| Strut | Stage | Crush load | Stroke |
|---|---|---|---|
| Primary | compression 1 | 4,500 lbf (20.0 kN) | 0–12 in (0.305 m) |
| Primary | compression 2 | 9,500 lbf (42.3 kN) | 12–32 in (0.508 m more) |
| Secondary | compression | 4,500 lbf (20.0 kN) | 0–14 in (0.356 m) |
| Secondary | tension 1 | 500 lbf (2.2 kN) | 0–6 in (0.152 m) |
| Secondary | tension 2 | 5,000 lbf (22.2 kN) | 6–18 in (0.305 m more) |

`LandingGear = crush` authors the loads as `newton:friction` and `mjc:frictionloss`, with a stiff friction impedance (`mjc:solimpfriction` 0.9999, `mjc:solreffriction` 4 ms) so the struts hold below their crush load instead of creeping, 20 kg of armature per stage, and `newton:limitStiffness` 1e7 N/m on the stage limits. `LandingGear = spring` keeps the same bodies with the secondaries locked and a 9e4 N/m spring on the primary, for simulators without joint friction. PhysX has no force-based joint friction, so under `Physics = physx` the crush stages behave as free strokes between their limits.

Touchdowns of the touchdown-mass LM (8.0 t) on rigid, flat ground, `--variants LandingGear=crush --drop 0`:

| Sink / drift | Slope | Primary crush, leading leg / side legs / trailing leg | Secondary tension | Nozzle clearance |
|---|---|---|---|---|
| 1.0 / 0.3 m/s | 0° | 78 / 54 / 35 mm | up to 32 mm | 0.15 m |
| 1.0 / 0.6 m/s | 10° | 111 / 57 / 22 mm | up to 39 mm | 0.14 m |
| 2.5 / 0.5 m/s | 0° | 221 / 189 / 162 mm | up to 68 mm | 0 (the J-mission nozzle extension, designed to crush, touches) |

All three land stable. On Apollo 11 the primaries did not stroke at all and the secondaries stroked up to 4.5 in (114 mm) in tension, because the soil absorbed about 60 % of the touchdown energy. The sim's rigid ground puts that energy into the primaries instead; a deformable regolith model is the next step.

### Touchdown example

`examples/newton/example_robot_lander_touchdown.py` drops any lander onto the surface in the Newton viewer. Every world gets the same drift, heading and slope; with `--world-count N`, the worlds land side by side with sink rates spread from `--vz` to `--vz-max`. The GUI shows each world's tilt and largest strut stroke, `r` re-drops, and `--test` prints per-strut peak and final strokes, tilt and nozzle clearance per world and fails if a lander tips:

```bash
cd examples/newton
../../.venv/bin/python example_robot_lander_touchdown.py --world-count 3 --vz 1.0 --vz-max 2.5 --vh 0.3
../../.venv/bin/python example_robot_lander_touchdown.py --variants LandingGear=spring --slope 10 --vh 0.6
../../.venv/bin/python example_robot_lander_touchdown.py --asset nova_c --variants "" --spacing 6 --vz 1.5 --slope 8
../../.venv/bin/python example_robot_lander_touchdown.py --viewer null --test --world-count 3 --vz 1.0 --vz-max 2.5
```

It defaults to `apollo_lm` with `LandingGear=crush`. Pass `--variants ""` for landers without that variant set.

The viewer panel has a control for every option:

| Group | Controls | Takes effect |
|---|---|---|
| Lander | asset (every `*/lander` config), each variant set the USD offers (`LandingGear`, `Propellant`, `Articulation`), physics flavour | rebuilds immediately |
| Lander | world count, substeps per frame | rebuilds on Rebuild |
| Touchdown | sink rate (first and last world), drift, drift heading, release height | on the next re-drop (`r` or Re-drop) |
| Touchdown | loop, re-drop every N s (`--loop N`) | live |
| Surface | slope (gravity), friction, world spacing | live |
| Surface | crush load scale (×0.1–3 on every crush stage, crush gear only) | live, for exploring softer or stiffer honeycomb |

### Rover examples

`examples/newton/example_robot_rover.py` drives any rover in the Newton viewer. It reads the joint roles from the USD:
- **Steering:** wheels with a `<corner>_steer` joint get Ackermann, crab and turn-in-place modes. Rovers without steering joints skid-steer.
- **Active suspension:** gets a ride-height control.
- **Servos:** every other servo (hatches, stairs, railings, wings, masts, dishes, arms) gets a slider.

Keys: `i`/`k` throttle, `j`/`l` steer, `space` stop, `m` steer mode, `u`/`o` ride height, `h` hatch, `t` stair, `g` latch.

```bash
cd examples/newton
../../.venv/bin/python example_robot_rover.py --asset ltv_concept --variants Crew=uncrewed,Payload=uncrewed
../../.venv/bin/python example_robot_rover.py --asset sev --speed 3
../../.venv/bin/python example_robot_rover.py --asset viper --viewer null --num-frames 300 --speed 0.7 --steer 10 --test
```

`examples/newton/example_robot_lunar_cruiser.py` showcases every joint on the Lunar Cruiser. Its sequences ease each joint through several steps:
- **Airlock:** spin the hand wheel two turns while the four latch bolts retract, then swing the hatch open.
- **Stair:** lower the upper flight, unfold the lower flight at the knee, then raise the railings. Stowing runs the steps in reverse.
- **Solar wings:** swing the wing boxes out to angles computed from the heading and a low polar sun (`--sun-az`, `--sun-el`).
- **Arm:** reach and stow.

The dish can track Earth, and the light sites are drawn as beams, because the Newton viewer does not render `UsdLux`. The GUI shows strut travel per wheel and ground speed. Keys: `1` airlock, `2` stair, `3` wings, `4` arm, `f` lights, `e` Earth tracking.

`--demo` plays the scripted showcase and `--test` checks the end state. `--record` saves every body pose to an `.npz`, which `scripts/playback.py` renders in Blender (EEVEE, real spot lights at every light site) for the video above:

```bash
cd examples/newton
../../.venv/bin/python example_robot_lunar_cruiser.py
../../.venv/bin/python example_robot_lunar_cruiser.py --viewer null --demo --num-frames 2820 --test --record ../../build/lunar_cruiser/demo_run.npz
cd ../.. && blender -b build/lunar_cruiser/lunar_cruiser.blend -P scripts/playback.py -- --asset lunar_cruiser --variant Solar:deployed --eevee --samples 32
```

```bash
.venv/bin/nvidia_usd_validate -D WeldChecker -D IndexedPrimvarChecker assets/blue_origin/mk1/lander/usd/mk1.usda
./pipeline.sh mk1 sim
.venv/bin/python scripts/sim_newton.py --asset mk1 --variants Offloader=crane --checks settle,servo
.venv/bin/python scripts/sim_newton.py --asset apollo_lm --variants LandingGear=crush --checks touchdown --drop 0 --td-vz 1.0 --td-vh 0.6 --slope 10
```

## Rebuild

You need Blender 5.2 on `PATH` (or set `BLENDER=/path/to/blender`) and a [uv](https://docs.astral.sh/uv/) venv:

```bash
uv venv --python 3.13 && uv pip install -r requirements.txt
```

```bash
./pipeline.sh list # assets, attachments first
./pipeline.sh mk1 # textures -> build -> export -> thumbnail -> USD package -> assets/ (full and simple)
./pipeline.sh mk1 package assets # selected steps: textures build export thumb package blend mesh simple assets gallery sim
./pipeline.sh update # every asset, attachments before their hosts
./pipeline.sh hero # every asset together -> docs/images/hero.jpg
./pipeline.sh lunar_cruiser gallery # Cycles renders -> docs/images/<asset path>/ (VIEWS=front_three_quarter,rear_three_quarter,wheel for rovers)
blender -b build/lunar_cruiser/lunar_cruiser.blend -P scripts/render.py -- --asset lunar_cruiser --views rear_patio --night --lights --pose airlock_hatch=1.75
.venv/bin/python scripts/render_rtx.py --asset lunar_cruiser --night --views rear_patio # Omniverse RTX path-traced render of the packaged USD (ovrtx)
./pipeline.sh scene # local assets/lunar_vehicles.usda referencing every asset's USD, to scale in one row (git-ignored)
./pipeline.sh web # web viewer models -> web/models/ (git-ignored)
./pipeline.sh serve # serve web/ at http://localhost:8000
./pipeline.sh release # update, then build the release zips in build/release/v<VERSION>/
```

`render.py` takes `--pose joint=value,...` for joint poses, `--variant Set:option` for geometry variants, `--night --lights` for a dark scene lit only by the asset's own lights, and `--sun az,el` for the sun direction. `pipeline.sh` points Blender's EEVEE/OpenGL at the NVIDIA GPU on hybrid-graphics laptops (Cycles uses OptiX either way).

Texture sets are cached by spec, so only changed sets regenerate. The 4096 px MLI sets take about 1.5 min each and peak around 6 GB of RAM, so run assets one at a time.

### Repository layout

| Path | Contents |
|---|---|
| `configs/<id>.py` | One config per asset: dimensions, materials, features, masses, colliders, `ASSET_PATH` |
| `families/` | Family builders shared by an asset family (`mk1`, `offloader`, `apollo_lm`, `nova_c`, `blue_ghost`, `peregrine`), plus `parts.py`: shared nozzles, sprung legs, thruster clusters, panels, dishes and lofts. `rover.py` builds every rover from its config: wheel modules (double wishbone, trailing arm, rocker, steering column, prismatic leg), wheel styles (airless spring, wire mesh, grousered, slat), extra jointed links and loop closures, a parts vocabulary (boxes, lofts, extrusions, panels, rails), crew stations, masts, dishes, solar arrays, arms and lights; `rover_kit.py` has the shared materials and helpers |
| `examples/newton/` | Newton examples: lander touchdown, any-rover driving, Lunar Cruiser showcase |
| `scripts/` | Pipeline: texture generation, Blender build, export, USD packaging, simple versions, renders, hero, release |
| `assets/<vendor>/<family>/<name>/` | Generated by the pipeline and committed with Git LFS: `usd/`, `gltf/`, `obj/`, `blender/`, `simple/`, `LICENSE`, `NOTICE` |
| `web/` | Static three.js viewer: `index.html`, `src/` (viewer and lil-gui panel), `vendor/three/` (pinned three.js r170 and lil-gui), `models/` (generated by `./pipeline.sh web`, git-ignored) |
| `docs/images/` | Hero and gallery renders |
| `refs/` | Local reference library (git-ignored) |
| `build/` | Intermediate outputs (git-ignored) |

To add a vehicle, write a family builder in `families/`, add `configs/<id>.py` with `FAMILY` and `ASSET_PATH = "<vendor>/<family>/<name>"`, and run `./pipeline.sh <id>`. It is picked up by `update`, `hero` and `release` automatically.

### Versions and releases

The version lives in `VERSION` and covers every asset. The packager stamps it into each USD as `assetInfo.version`, `isaac:version` and `asset_version` in the root layer's `customLayerData` and `SimReady_Metadata`.

To cut a release:

1. Bump `VERSION` and run `./pipeline.sh release`. It rebuilds every asset, refreshes `assets/`, and builds the release zips in `build/release/v<VERSION>/` so you can check them.
2. Commit `assets/` and `VERSION`, tag the commit `v<VERSION>`, and push the tag.
3. The [release workflow](.github/workflows/release.yml) runs on the tag. It checks that the tag matches `VERSION` and every stamped USD, zips the committed assets, builds `web-models.zip` for the web viewer, publishes the GitHub release with `SHA256SUMS`, and starts the pages workflow to deploy the viewer for that release.

## Roadmap

- **Blue Moon MK2** (crewed HLS): a new `mk2` family with a crew cabin, hatch and stair platform, four telescoping legs, two oblate tanks in a truss cage, the LH2 dome with sunshield panels, two gimballed dishes on top and three BE-7s.
- **More landers**, such as Astrobotic Griffin, ispace / Draper APEX 1.0 and Intuitive Machines Nova-D, under their own vendor folders.

## Sources

Geometry and dimensions come from public sources: NASA public-domain photos, published manufacturer and NASA specifications, scale drawings and regulatory filings. Manufacturer renders are used only as visual references. Many details are inferred from photos and are estimates. For Blue Moon MK1:

- **RCS.** Thruster count, thrust and pod geometry are not published; the layout follows photos and renders.
- **BE-7.** Nozzle size and gimbal range are estimates.
- **Mass and legs.** Leg stroke, spring rate, touchdown and dry masses are assumed; the launch mass is published.
- **High-gain antenna.** Its existence comes from the FCC filing and press; placement and size are assumed.
- **Offloader.** Its design is not published; the geometry follows a Blue Origin render and the dimensions are estimates.

For the rovers, the most reliable numbers are official specifications. Elsewhere, positions are measured from photos and renders against a known dimension and are estimates (typically ±5–15 %):

- **Lunar Cruiser.** Official figures come from JAXA's 2025 specification slide: 6.44 × 4.84 × 4.85 m, wheelbase 3.81 m, track 3.20 m, ≤ 15 t at launch and ≤ 18 t loaded, 4 × 10 m solar wings, and a 1.0 × 1.5 m hatch. Everything else is calibrated on those figures from the NASA/JAXA 2025 renders: windscreen, lamps, rear patio, stair, stowage, gas bottles and the arm. Suspension and steering are not published; independent wishbones with a steering front axle are assumed.
- **LTVs.** CLV-1 and Pegasus dimensions are measured from NASA photos and renders; the mass caps are official. FLEX dimensions come from Astrolab's payload interface guide. The Moon RACER and Eagle are measured from photos, and the Moon RACER's published 3.9 m width is read as including its panels.
- **SEV, VIPER, CADRE.** These come from NASA and JPL fact sheets and slides: SEV mass, wheelbase and height; VIPER's 1.7 × 1.7 × 2.5 m, 447 kg, 0.5 m wheels and mobility ranges; CADRE's 0.546 × 0.385 × 0.235 m and 8.6 kg. Suitport, docking hatch and instrument positions are measured from photos.
- **FLIP and MAPP.** No official dimensions beyond mass and the Venturi wheel diameter (FLIP) or the 45 × 38 × 40 cm envelope (MAPP); the geometry is measured from renders.
- **Concepts.** `ltv_concept` follows the NASA LTV requirements (2 suited crew plus 250 kg, or 1,600 kg uncrewed). `pr_concept` follows typical pressurised-rover features: 0.6 × 0.9 m suitports, an IDSS docking ring, a forward window band, radiators and a 2–3 m arm.

For the other landers:

- **Apollo LM.** Landing-gear kinematics and crush loads follow NASA TN D-6850, "Apollo Experience Report: Lunar Module Landing Gear Subsystem" (Rogers, 1972), and the 1973 NASA landing-gear paper. Stage, deck and engine heights, the 31 ft gear span, 37 in pads, ascent-stage envelope and propulsion data come from the Grumman LM Structures Study Guide, the Apollo News Reference and a dimensioned NASA 3-view, converted from LM stations. The leg apex, RCS quad and antenna positions are measured from those drawings (±0.1–0.3 m), the touchdown mass is an estimate, and the lunar-surface sensing probes are left off so the asset stands at z = 0.
- **Nova-C.** Height (4.3 m), 1.6 m hull, 4.6 m gear, masses, VR900 Isp and gimbal, helium cold-gas RCS, three arrays and the fixed high-gain antenna come from the IM-1 press kit and FCC filing. Leg stroke, RCS count, gimbal range and the faces carrying the nav pod and antennas are assumptions.
- **Blue Ghost.** The 2 m height, 3.5 m span, 1,517 kg launch and 469 kg dry masses, LEROS 4-ET engine, 8 Spectre RCS and 12 cold-gas thrusters come from Firefly and NASA; the span is read as the footpad-centre diagonal. Body, tank and leg geometry is measured from Firefly renders (±10 %). The flight unit's MLI is copper, not the gold of the renders.
- **Peregrine.** Height, 2.5 m width (read as face-on footpad spacing), 1,283 kg wet mass, engine and ACS counts and the payload-deck drawing come from Astrobotic's payload user's guide and post-mission report. Positions, tank sizes and the dry mass (a rocket-equation estimate) are inferred. The flown vehicle wore silver MLI.

## License

Copyright 2026 Alex Maietta (see [`NOTICE`](NOTICE)).

- **Code** (`scripts/`, `families/`, `configs/`, `pipeline.sh`): [Apache License 2.0](LICENSE).
- **Model assets** (`assets/`, each asset folder carries its own `LICENSE` and `NOTICE`) and **renders** (`docs/images/`): [Creative Commons Attribution 4.0 International (CC BY 4.0)](LICENSE-ASSETS). Credit: "Lunar surface mobility assets by Alex Maietta".

This project is not affiliated with or endorsed by Blue Origin, NASA or any other vehicle manufacturer. Vehicle and company names are trademarks of their owners and are used only to identify the vehicles modelled; manufacturer logos and wordmarks are left off the models.
