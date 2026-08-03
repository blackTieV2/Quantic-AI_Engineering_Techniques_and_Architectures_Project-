from __future__ import annotations

import base64
import hashlib
import io
import shutil
import tarfile
from pathlib import Path

EXPECTED_SHA256 = "54037c1d0f97b13da37a989688179449490a9bee1bccb78eac1c4a638094345e"


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parts = sorted((root / ".score5").glob("payload.*"))
    if len(parts) != 5:
        raise SystemExit(f"expected 5 payload files, found {len(parts)}")

    encoded = "".join(part.read_text(encoding="utf-8") for part in parts)
    archive = base64.b64decode(encoded.encode("ascii"), validate=True)
    actual = hashlib.sha256(archive).hexdigest()
    if actual != EXPECTED_SHA256:
        raise SystemExit(f"archive checksum mismatch: {actual} != {EXPECTED_SHA256}")

    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as package:
        members = package.getmembers()
        root_resolved = root.resolve()
        for member in members:
            destination = (root / member.name).resolve()
            if destination != root_resolved and root_resolved not in destination.parents:
                raise SystemExit(f"unsafe archive path: {member.name}")

        for child in root.iterdir():
            if child.name == ".git":
                continue
            if child.is_dir():
                shutil.rmtree(child)
            else:
                child.unlink()

        try:
            package.extractall(root, members=members, filter="data")
        except TypeError:
            package.extractall(root, members=members)

    print(f"Expanded {len(members)} verified project files from SHA256 {actual}")


if __name__ == "__main__":
    main()
