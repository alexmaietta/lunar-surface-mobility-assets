import argparse
import subprocess
import sys

LFS_HINT = "git lfs track '<pattern>' (or add it to .gitattributes), then git rm --cached <file> && git add <file>"


def index_blobs():
    out = subprocess.run(["git", "ls-files", "-s", "-z"], capture_output=True, check=True).stdout.decode()
    blobs = {}
    for rec in filter(None, out.split("\0")):
        meta, path = rec.split("\t", 1)
        mode, sha, _stage = meta.split()
        if mode != "160000":
            blobs[path] = sha
    return blobs


def blob_sizes(shas):
    if not shas:
        return {}
    res = subprocess.run(["git", "cat-file", "--batch-check=%(objectname) %(objectsize)"], input="\n".join(shas).encode(),
                         capture_output=True, check=True).stdout.decode()
    return {sha: int(size) for sha, size in (line.split() for line in res.splitlines())}


def main():
    ap = argparse.ArgumentParser(description="Fail if any staged or tracked file is stored in git (not LFS) above a size limit.")
    ap.add_argument("--limit-mb", type=float, default=4.0)
    a = ap.parse_args()
    blobs = index_blobs()
    sizes = blob_sizes(sorted(set(blobs.values())))
    limit = a.limit_mb * 1024 * 1024
    big = sorted(((sizes[sha], path) for path, sha in blobs.items() if sizes.get(sha, 0) > limit), reverse=True)
    total = sum(sizes.values())
    if big:
        print(f"{len(big)} file(s) over {a.limit_mb:g} MB would be stored in git instead of LFS:")
        for size, path in big[:50]:
            print(f"  {size / 1048576:8.1f} MB  {path}")
        print(f"fix: {LFS_HINT}")
        sys.exit(1)
    print(f"ok: {len(blobs)} files, {total / 1048576:.1f} MB of git objects, none over {a.limit_mb:g} MB outside LFS")


if __name__ == "__main__":
    main()
