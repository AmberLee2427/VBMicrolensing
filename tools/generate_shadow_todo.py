# tools/generate_shadow_todo.py
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import re


WARNING_PATTERN = re.compile(r"(.*):(\d+):(\d+): warning: (.*)")
FUNC_PATTERN = re.compile(r"VBMicrolensing::([A-Za-z0-9_~]+)\s*\(")


def load_file_lines(path: Path) -> list[str]:
    return path.read_text().splitlines()


def resolve_function(file_path: Path, line_no: int, cache: dict[Path, list[str]]) -> str:
    if file_path not in cache:
        cache[file_path] = load_file_lines(file_path)
    lines = cache[file_path]
    idx = min(max(line_no - 1, 0), len(lines) - 1)

    # Scan upwards to find the nearest VBMicrolensing::Function definition
    for i in range(idx, -1, -1):
        text = lines[i]
        if "VBMicrolensing::" in text:
            m = FUNC_PATTERN.search(text)
            if m:
                return m.group(1)
    return "GLOBAL"


def main() -> None:
    log_path = Path("results/shadow_report.txt")
    if not log_path.exists():
        raise FileNotFoundError("results/shadow_report.txt not found; run the shadow report first")

    entries: dict[str, set[tuple[str, int, str]]] = defaultdict(set)
    file_cache: dict[Path, list[str]] = {}

    for line in log_path.read_text().splitlines():
        m = WARNING_PATTERN.match(line)
        if not m:
            continue
        file_name, lineno_s, _, message = m.groups()
        if "shadow" not in message.lower():
            continue
        path = Path(file_name)
        try:
            function = resolve_function(path, int(lineno_s), file_cache)
        except (OSError, UnicodeDecodeError):
            function = "GLOBAL"
        key = (str(path), int(lineno_s), message.strip())
        entries[function].add(key)

    output_lines = ["# Shadow Diagnostics TODO", ""]
    total = 0
    for function in sorted(entries.keys()):
        output_lines.append(f"## {function}")
        for file_name, lineno, message in sorted(entries[function]):
            output_lines.append(f"- [ ] `{file_name}:{lineno}` – {message}")
            total += 1
        output_lines.append("")

    Path("docs/ShadowTODO.md").write_text("\n".join(output_lines))
    print(f"Wrote {total} entries grouped by function to docs/ShadowTODO.md")


if __name__ == "__main__":
    main()
