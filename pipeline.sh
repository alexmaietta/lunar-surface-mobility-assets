#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
export BLENDER=${BLENDER:-$(command -v blender || echo "$HOME/.local/bin/blender")}
if [ -f /usr/share/glvnd/egl_vendor.d/10_nvidia.json ]; then
  export __EGL_VENDOR_LIBRARY_FILENAMES=${__EGL_VENDOR_LIBRARY_FILENAMES:-/usr/share/glvnd/egl_vendor.d/10_nvidia.json}
  export __NV_PRIME_RENDER_OFFLOAD=${__NV_PRIME_RENDER_OFFLOAD:-1} __GLX_VENDOR_LIBRARY_NAME=${__GLX_VENDOR_LIBRARY_NAME:-nvidia}
fi
PY=${PY:-.venv/bin/python}

usage() {
  cat <<EOF
usage: ./pipeline.sh <asset> [step ...]   steps: textures build export thumb package blend mesh simple assets gallery sim (default: all)
       ./pipeline.sh <command>            commands: update hero release list scene web serve
assets: $(order | tr '\n' ' ')
EOF
  exit 1
}

order() {
  $PY - <<'EOF'
import glob, os, sys
sys.path.insert(0, "scripts")
import assetcfg
ids = sorted(os.path.splitext(os.path.basename(p))[0] for p in glob.glob("configs/*.py"))
deps = {a: [d for opts in getattr(assetcfg.load(a), "ATTACHMENTS", {}).values() for d, _, _ in opts.values()] for a in ids}
done = []
def visit(a):
    if a not in done:
        [visit(d) for d in deps[a]]
        done.append(a)
[visit(a) for a in ids]
print("\n".join(done))
EOF
}

asset_path() { $PY -c "import sys; sys.path.insert(0, 'scripts'); import assetcfg; print(assetcfg.load('$1').ASSET_PATH)"; }

textures() { $PY scripts/textures.py --asset "$asset"; }
build()    { $BLENDER -b --factory-startup -P scripts/build.py -- --asset "$asset"; }
export_()  { $BLENDER -b "$blend" -P scripts/export.py -- --asset "$asset" --lod full
             $BLENDER -b "$blend" -P scripts/export.py -- --asset "$asset" --lod proxy
             $BLENDER -b "$blend" -P scripts/export.py -- --asset "$asset" --lod simple; }
thumb()    { $BLENDER -b "$blend" -P scripts/render.py -- --asset "$asset" --views thumb --samples 64 --res 256x256 \
               --out "build/$asset/renders" && mv "build/$asset/renders/thumb.png" "build/$asset/renders/thumb_256.png"; }
package()  { $PY scripts/package.py --asset "$asset"; }
blend_()   { $BLENDER -b "$blend" -P scripts/export_blend.py -- --asset "$asset"; }
mesh()     { $BLENDER -b "$blend" -P scripts/export_mesh.py -- --asset "$asset"; }
simple()   { $BLENDER -b "$blend" -P scripts/export_simple.py -- --asset "$asset"; }
assets()   { $PY scripts/publish.py --asset "$asset" && blend_ && mesh && simple; }
gallery()  { local dst="docs/images/$(asset_path "$asset")"
             rm -rf "build/$asset/gallery"
             $BLENDER -b "$blend" -P scripts/render.py -- --asset "$asset" --samples 256 --res 1600x1200 \
               --views "${VIEWS:-front_three_quarter,side,low_engine,top_deck,lunar}" \
               --out "build/$asset/gallery"
             for att in $($PY -c "import sys; sys.path.insert(0, 'scripts'); import assetcfg
for s, o in getattr(assetcfg.load('$asset'), 'ATTACHMENTS', {}).items(): print(*(f'{s}:{k}' for k in o))"); do
               $BLENDER -b "$blend" -P scripts/render.py -- --asset "$asset" --attach "$att" --samples 256 --res 1600x1200 \
                 --views front_three_quarter,side,top_deck --out "build/$asset/gallery/${att#*:}"
             done
             mkdir -p "$dst" && rsync -a --delete "build/$asset/gallery/" "$dst/"; }
sim()      { $PY scripts/sim_newton.py --asset "$asset"; }
all()      { textures; build; export_; thumb; package; assets; }

update()  { for asset in $(order); do blend=build/$asset/$asset.blend; all; done; }
hero()    { $BLENDER -b --factory-startup -P scripts/hero.py -- --out docs/images/hero.jpg; }
release() { update; $PY scripts/make_release.py; v=$(cat VERSION)
            echo "next: git add -A assets VERSION && git commit -m \"Release v$v\" && git tag v$v && git push origin main v$v"; }
list()    { order; }
scene()   { $PY scripts/scene.py; }
web()     { $PY scripts/web_export.py; }
serve()   { echo "web viewer: http://localhost:${PORT:-8000}"; $PY -m http.server -d web "${PORT:-8000}"; }

[ $# -ge 1 ] || usage
case $1 in
  update|hero|release|list|scene|web|serve) $1; exit ;;
esac
[ -f "configs/$1.py" ] || usage
asset=$1; shift
blend=build/$asset/$asset.blend
for step in "${@:-all}"; do
  case $step in
    export) export_ ;;
    blend) blend_ ;;
    textures|build|thumb|package|mesh|simple|assets|gallery|sim|all) $step ;;
    *) usage ;;
  esac
done
