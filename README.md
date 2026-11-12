[![Latest release](https://img.shields.io/github/v/release/alexmaietta/lunar-surface-mobility-assets?label=release)](https://github.com/alexmaietta/lunar-surface-mobility-assets/releases/latest)
[![Code: BSD-3-Clause](https://img.shields.io/badge/code-BSD--3--Clause-blue.svg)](LICENSE)
[![Assets: CC0 1.0](https://img.shields.io/badge/assets-CC0%201.0-lightgrey.svg)](LICENSE-ASSETS)
![USD](https://img.shields.io/badge/format-OpenUSD-6a5acd.svg)
![URDF](https://img.shields.io/badge/format-URDF-22314e.svg?logo=ros&logoColor=white)
![Blender](https://img.shields.io/badge/format-Blender-e87d0d.svg?logo=blender&logoColor=white)
![glTF](https://img.shields.io/badge/format-glTF-87c540.svg)
![OBJ](https://img.shields.io/badge/format-OBJ-555555.svg)

# Lunar Surface Mobility Assets

![Lunar surface mobility assets on the lunar surface](docs/images/hero.jpg)

These are simulation-ready models of lunar landers, rovers and their friends. 

Each one is built procedurally in Blender from public references and gets generated, high-resolution, tileable PBR textures. It ships as an Isaac Sim / SimReady-style **USD** asset with physics, joints, colliders and named sites for engines, RCS thrusters, sensors and antennas. The rovers add drive, steering and suspension joints, working hatches, stairs and arms, and real lights. Every asset is also a **URDF** robot description with per-link mass and inertia, colliders, joint limits and closed suspension linkages, and comes as **glTF**, **OBJ** and **Blender** too.

**[Explore every model in 3D](https://alexmaietta.github.io/lunar-surface-mobility-assets/)** We also provide an interactive viewer to orbit around the assets, select any vehicle for its specs, and drive its moving parts, such as antennas, arms, hatches, stairs, steering and wheels.

| Vendor | Vehicle | Asset |
|---|---|---|
| Blue Origin | [Blue Moon MK1](assets/blue_origin/mk1/lander) lander | [`mk1`](https://github.com/alexmaietta/lunar-surface-mobility-assets/releases/latest/download/mk1-usd.zip) |
| Blue Origin | [Blue Moon MK1](assets/blue_origin/mk1/offloader) payload offloader | [`mk1_offloader`](https://github.com/alexmaietta/lunar-surface-mobility-assets/releases/latest/download/mk1_offloader-usd.zip) |
| Grumman / NASA | [Apollo Lunar Module](assets/grumman/apollo_lm/lander) (J-mission) | [`apollo_lm`](https://github.com/alexmaietta/lunar-surface-mobility-assets/releases/latest/download/apollo_lm-usd.zip) |
| Intuitive Machines | [Nova-C](assets/intuitive_machines/nova_c/lander) (IM-1 / IM-2) | [`nova_c`](https://github.com/alexmaietta/lunar-surface-mobility-assets/releases/latest/download/nova_c-usd.zip) |
| Firefly Aerospace | [Blue Ghost](assets/firefly/blue_ghost/lander) (Mission 1) | [`blue_ghost`](https://github.com/alexmaietta/lunar-surface-mobility-assets/releases/latest/download/blue_ghost-usd.zip) |
| Astrobotic | [Peregrine](assets/astrobotic/peregrine/lander) (Mission One) | [`peregrine`](https://github.com/alexmaietta/lunar-surface-mobility-assets/releases/latest/download/peregrine-usd.zip) |
| Toyota / JAXA | [Lunar Cruiser](assets/toyota_jaxa/lunar_cruiser/rover) pressurised rover (2025 design) | [`lunar_cruiser`](https://github.com/alexmaietta/lunar-surface-mobility-assets/releases/latest/download/lunar_cruiser-usd.zip) |
| NASA | [Space Exploration Vehicle](assets/nasa/sev/rover) (SEV / LER, 2010) | [`sev`](https://github.com/alexmaietta/lunar-surface-mobility-assets/releases/latest/download/sev-usd.zip) |
| NASA | [VIPER](assets/nasa/viper/rover) | [`viper`](https://github.com/alexmaietta/lunar-surface-mobility-assets/releases/latest/download/viper-usd.zip) |
| NASA | [IPEx](assets/nasa/ipex/rover) regolith excavator (TRL 5/6) | [`ipex`](https://github.com/alexmaietta/lunar-surface-mobility-assets/releases/latest/download/ipex-usd.zip) |
| NASA / JPL | [CADRE](assets/nasa_jpl/cadre/rover) rover (IM-3) | [`cadre`](https://github.com/alexmaietta/lunar-surface-mobility-assets/releases/latest/download/cadre-usd.zip) |
| Astrolab | [FLEX](assets/astrolab/flex/rover) prototype | [`flex`](https://github.com/alexmaietta/lunar-surface-mobility-assets/releases/latest/download/flex-usd.zip) |
| Astrolab | [CLV-1](assets/astrolab/clv1/rover) LTV (NASA task order 2026) | [`clv1`](https://github.com/alexmaietta/lunar-surface-mobility-assets/releases/latest/download/clv1-usd.zip) |
| Astrolab | [FLIP](assets/astrolab/flip/rover) (Griffin-1) | [`flip`](https://github.com/alexmaietta/lunar-surface-mobility-assets/releases/latest/download/flip-usd.zip) |
| Lunar Outpost | [Pegasus](assets/lunar_outpost/pegasus/rover) LTV (NASA task order 2026) | [`pegasus`](https://github.com/alexmaietta/lunar-surface-mobility-assets/releases/latest/download/pegasus-usd.zip) |
| Lunar Outpost | [Eagle](assets/lunar_outpost/eagle/rover) LTV bid | [`eagle`](https://github.com/alexmaietta/lunar-surface-mobility-assets/releases/latest/download/eagle-usd.zip) |
| Lunar Outpost | [MAPP](assets/lunar_outpost/mapp/rover) (IM-2) | [`mapp`](https://github.com/alexmaietta/lunar-surface-mobility-assets/releases/latest/download/mapp-usd.zip) |
| Intuitive Machines | [Moon RACER](assets/intuitive_machines/moon_racer/rover) LTV bid | [`moon_racer`](https://github.com/alexmaietta/lunar-surface-mobility-assets/releases/latest/download/moon_racer-usd.zip) |
| Concept | [Lunar Terrain Vehicle](assets/concepts/ltv/rover), crewed or uncrewed | [`ltv_concept`](https://github.com/alexmaietta/lunar-surface-mobility-assets/releases/latest/download/ltv_concept-usd.zip) |
| Concept | [Pressurised rover](assets/concepts/pressurized/rover) | [`pr_concept`](https://github.com/alexmaietta/lunar-surface-mobility-assets/releases/latest/download/pr_concept-usd.zip) |
| Blue Origin | [Blue Moon MK2](assets/blue_origin/mk2/lander) crewed lander (Artemis HLS) | [`mk2`](https://github.com/alexmaietta/lunar-surface-mobility-assets/releases/latest/download/mk2-usd.zip) |
| ASI / Thales Alenia Space | [Multi-Purpose Habitation (MPH)](assets/asi_thales/mph/habitat) mobile surface habitat (2025 reference design) | [`mph`](https://github.com/alexmaietta/lunar-surface-mobility-assets/releases/latest/download/mph-usd.zip) |

## Quick Start

Each asset is released as `<asset>-usd.zip`, `<asset>-urdf.zip`, `<asset>-gltf.zip`, `<asset>-obj.zip` and `<asset>-blend.zip` on the [latest release](https://github.com/alexmaietta/lunar-surface-mobility-assets/releases/latest). 

For small downloads, `<asset>-simple-usd.zip`, `<asset>-simple-gltf.zip` and `<asset>-simple-obj.zip` hold a single simplified mesh of a few hundred kB (see [Simple versions](#simple-versions)). To pin a version, use `download/v0.1.0` instead of `latest/download`; each release includes `SHA256SUMS`.

```sh
curl -LO https://github.com/alexmaietta/lunar-surface-mobility-assets/releases/latest/download/mk1-usd.zip
unzip mk1-usd.zip # -> mk1/mk1.usda
curl -LO https://github.com/alexmaietta/lunar-surface-mobility-assets/releases/latest/download/eagle-urdf.zip
unzip eagle-urdf.zip # -> eagle/urdf/eagle.urdf (+ meshes, eagle/obj textures)
curl -LO https://github.com/alexmaietta/lunar-surface-mobility-assets/releases/latest/download/mk1-simple-gltf.zip
unzip mk1-simple-gltf.zip # -> mk1_simple/mk1_simple.glb
```

Or clone the repo. The same assets are in `assets/`, stored with Git LFS (set `GIT_LFS_SKIP_SMUDGE=1` to skip them):

```sh
git clone git@github.com:alexmaietta/lunar-surface-mobility-assets.git
cd lunar-surface-mobility-assets
git lfs pull
```

## Gallery

![Blue Moon MK2 to scale next to the LTV concept, Apollo LM, Blue Moon MK1 and Lunar Cruiser](docs/images/blue_origin/mk2/lander/scale_lineup.jpg)

| | |
|---|---|
| ![MK2 front three-quarter](docs/images/blue_origin/mk2/lander/front_three_quarter.jpg) | ![MK2 side](docs/images/blue_origin/mk2/lander/side.jpg) |
| ![MK2 crew door open, egress platform and stair](docs/images/blue_origin/mk2/lander/crew_door.jpg) | ![MK2 docking hatch, windows and engine skirt](docs/images/blue_origin/mk2/lander/low_engine.jpg) |
| ![MK1 front three-quarter](docs/images/blue_origin/mk1/lander/front_three_quarter.jpg) | ![MK1 side](docs/images/blue_origin/mk1/lander/side.jpg) |
| ![MK1 engine and legs](docs/images/blue_origin/mk1/lander/low_engine.jpg) | ![MK1 deck](docs/images/blue_origin/mk1/lander/top_deck.jpg) |
| ![MK1 with the offloader](docs/images/blue_origin/mk1/lander/crane/front_three_quarter.jpg) | ![MK1 offloader](docs/images/blue_origin/mk1/offloader/lunar.jpg) |
| ![Apollo LM front three-quarter](docs/images/grumman/apollo_lm/lander/front_three_quarter.jpg) | ![Apollo LM descent engine and legs](docs/images/grumman/apollo_lm/lander/low_engine.jpg) |
| ![Nova-C front three-quarter](docs/images/intuitive_machines/nova_c/lander/front_three_quarter.jpg) | ![Nova-C engine and legs](docs/images/intuitive_machines/nova_c/lander/low_engine.jpg) |
| ![Blue Ghost front three-quarter](docs/images/firefly/blue_ghost/lander/front_three_quarter.jpg) | ![Blue Ghost side](docs/images/firefly/blue_ghost/lander/side.jpg) |
| ![Peregrine front three-quarter](docs/images/astrobotic/peregrine/lander/front_three_quarter.jpg) | ![Peregrine side](docs/images/astrobotic/peregrine/lander/side.jpg) |

### Rovers

![Lunar Cruiser sequence](docs/images/toyota_jaxa/lunar_cruiser/rover/sequence.gif)

| | | |
|---|---|---|
| ![Lunar Cruiser front three-quarter](docs/images/toyota_jaxa/lunar_cruiser/rover/front_three_quarter.jpg) | ![Lunar Cruiser rear patio, stair deployed](docs/images/toyota_jaxa/lunar_cruiser/rover/rear_patio.jpg) | ![Lunar Cruiser airlock open, latch bolts retracted](docs/images/toyota_jaxa/lunar_cruiser/rover/airlock_open.jpg) |
| ![Lunar Cruiser solar wings deployed toward a low sun](docs/images/toyota_jaxa/lunar_cruiser/rover/solar_deployed.jpg) | ![Lunar Cruiser rear patio at night under its own lights](docs/images/toyota_jaxa/lunar_cruiser/rover/rear_patio_night.jpg) | ![Lunar Cruiser wheels and sponson](docs/images/toyota_jaxa/lunar_cruiser/rover/wheel.jpg) |

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
| ![NASA IPEx front three-quarter](docs/images/nasa/ipex/rover/front_three_quarter.jpg) | ![NASA IPEx rear three-quarter](docs/images/nasa/ipex/rover/rear_three_quarter.jpg) | ![NASA IPEx at night](docs/images/nasa/ipex/rover/night.jpg) |
| ![NASA JPL CADRE front three-quarter](docs/images/nasa_jpl/cadre/rover/front_three_quarter.jpg) | ![NASA JPL CADRE rear three-quarter](docs/images/nasa_jpl/cadre/rover/rear_three_quarter.jpg) | ![NASA JPL CADRE at night](docs/images/nasa_jpl/cadre/rover/night.jpg) |

| | | |
|---|---|---|
| ![NASA VIPER driving at night under its NavLights](docs/images/nasa/viper/rover/night_drive.jpg) | ![VIPER left NavCam view, RTX spectral](docs/images/nasa/viper/rover/nav_cam_left_spectral.jpg) | ![VIPER front-left HazCam view, RTX spectral](docs/images/nasa/viper/rover/haz_cam_fl_spectral.jpg) |
| ![NASA VIPER mast head, NavCams, NavLights and HGA](docs/images/nasa/viper/rover/mast.jpg) | ![NASA VIPER wheel module](docs/images/nasa/viper/rover/wheel.jpg) | |

| | |
|---|---|
| ![NASA IPEx digging with the radiator cover open](docs/images/nasa/ipex/rover/digging.jpg) | ![NASA IPEx wheels and bucket drums](docs/images/nasa/ipex/rover/wheel.jpg) |

### Habitats

| | | |
|---|---|---|
| ![MPH front three-quarter, solar blankets raised](docs/images/asi_thales/mph/habitat/front_three_quarter.jpg) | ![MPH docking end and rear three-quarter](docs/images/asi_thales/mph/habitat/rear_three_quarter.jpg) | ![MPH stowed for driving](docs/images/asi_thales/mph/habitat/stowed_for_driving.jpg) |
| ![MPH EVA door open above the porch and ladder](docs/images/asi_thales/mph/habitat/eva_door_open.jpg) | ![MPH EVA end at night under its own lights](docs/images/asi_thales/mph/habitat/eva_end_night.jpg) | ![MPH wheels and bogies](docs/images/asi_thales/mph/habitat/wheel.jpg) |

## Web viewer

`web/` is a static, interactive 3D viewer of every asset.

- **Fast first load.** It loads the simple version of every asset (11 MB for all of them) in the same line-up as the hero render, with a 1.8 m human for scale.
- **Detailed models.** Once the previews are up, every web-optimised model loads in the background, smallest first, and replaces its preview (85 MB in total; 0.8–5.9 MB each: the full glTF with textures resized to 1024 px and re-encoded as WebP via `EXT_texture_webp`). Clicking a vehicle, choosing it in the panel, or opening `#<asset id>` moves it to the front of the queue and flies the camera to it. Add `?lite` to the URL to load detailed models only on demand.
- **Specs.** Height, footprint, mass states, main engines, thruster counts, joints, plus links to the source files and release downloads.
- **Moving parts.** A slider for every controllable joint, grouped by role: engine gimbals, steering, antennas, cameras, robotic arms, cranes, hatches, latches, stairs, solar arrays and deployables. Wheels have a spin control, and Animate sweeps every joint through its range. Joint axes and limits come from the USD physics layer. Passive joints (landing gear, suspension and loop-closed linkages) are left to simulation.
- **Attachments.** These can be toggled per host, for example the MK1 offloader crane.

Build the models and serve the site locally:

```bash
./pipeline.sh web # assets/ -> web/models/ (preview.glb, full.glb, manifest.json per asset; git-ignored)
./pipeline.sh serve # http://localhost:8000 (PORT=8080 to change)
```

## License

Copyright 2026 Alex Maietta (see [`NOTICE`](NOTICE)).

- **Code** (`scripts/`, `families/`, `configs/`, `examples/`, `web/` except `web/vendor/`, `pipeline.sh`) is under the [BSD 3-Clause License](LICENSE). Third-party code in `web/vendor/` keeps its own license.
- **Model assets** (`assets/`, each asset folder carries its own `LICENSE` and `NOTICE`) and **renders** (`docs/images/`) are dedicated to the public domain under [CC0 1.0 Universal](LICENSE-ASSETS). Use them for anything without asking or crediting. A credit such as "Lunar surface mobility assets by Alex Maietta" is appreciated but not required.

This project is not affiliated with or endorsed by Blue Origin, NASA or any other vehicle manufacturer. Vehicle and company names are trademarks of their owners and are used only to identify the vehicles modelled. Manufacturer logos and wordmarks are left off the models.
