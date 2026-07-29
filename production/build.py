

"""
Production Subsystem
----------------------
Build/export tooling: bundles the current world state, generated assets,
and a manifest into a distributable package. Also handles asset schema
validation so procedurally generated content stays structurally consistent
across sessions.
"""
import json, os, zipfile, hashlib, time

class AssetManifest:
    def __init__(self):
        self.entries = []

    def add(self, path, category):
        h = hashlib.sha256()
        with open(path, "rb") as f:
            h.update(f.read())
        self.entries.append({
            "path": path,
            "category": category,
            "sha256": h.hexdigest()[:16],
            "size_bytes": os.path.getsize(path),
        })

    def to_dict(self):
        return {"generated_at": time.time(), "assets": self.entries}

    def save(self, path):
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)


def validate_dungeon_schema(dungeon):
    required = {"depth", "rooms"}
    if not required.issubset(dungeon):
        return False, f"missing keys: {required - set(dungeon)}"
    for room in dungeon["rooms"]:
        if not {"room_id", "size", "connections", "encounter"}.issubset(room):
            return False, f"room {room.get('room_id')} malformed"
    return True, "ok"


def build_package(source_dir, output_zip, manifest_path=None):
    manifest = AssetManifest()
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(source_dir):
            for fname in files:
                fpath = os.path.join(root, fname)
                arcname = os.path.relpath(fpath, source_dir)
                zf.write(fpath, arcname)
                manifest.add(fpath, category=os.path.splitext(fname)[1].lstrip("."))
    if manifest_path:
        manifest.save(manifest_path)
    return output_zip, manifest.to_dict()


