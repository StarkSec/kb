#!/usr/bin/env python3
"""
Usage:
  kb                          show top-level tree
  kb <keywords...>            search by keywords in any order
  kb help <N>                 expanded view of command N from last search
  kb list                     alias for no-args tree view
"""

import json
import sys
from pathlib import Path

# colours with ansi
RESET  = "\033[0m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
CYAN   = "\033[38;5;81m"
YELLOW = "\033[38;5;221m"
GRAY   = "\033[38;5;245m"
WHITE  = "\033[38;5;252m"
RED    = "\033[38;5;203m"

KB_DIR = Path.home() / "kb"

# Last search results — persisted to disk so `kb help N` works across invocations
_last_listed: list[dict] = []
_LAST_RESULTS_FILE = Path("/tmp/.kb_last_results.json")


def _save_last(results: list[dict]) -> None:
    try:
        _LAST_RESULTS_FILE.write_text(json.dumps(results))
    except Exception:
        pass


def _load_last() -> list[dict]:
    if _LAST_RESULTS_FILE.exists():
        return json.loads(_LAST_RESULTS_FILE.read_text())
    return []


def _load_all() -> dict[str, dict]:
    if not KB_DIR.is_dir():
        print(f"{RED}[-]{RESET} {KB_DIR} does not exist")
        sys.exit(1)

    result = {}
    for path in sorted(KB_DIR.glob("*.json")):
        name = path.stem
        try:
            result[name] = json.loads(path.read_text())
        except json.JSONDecodeError as e:
            print(f"{RED}[-]{RESET} Failed to parse {path.name}: {e}")
    return result


def _collect_entries(node: dict, path: list[str], file_name: str,
                     out: list[dict]) -> None:
    """Walk the tree recursively. Any node with a 'cmd' key is a leaf entry."""
    if "cmd" in node:
        # path[0] is the wrapper key (e.g. "enum") — skip it in breadcrumb
        # path[-1] is the numeric id — skip it too, used only for ordering
        display_path = path[1:-1] if len(path) > 2 else path[1:]
        out.append({
            "file":       file_name,
            "path":       list(path),
            "breadcrumb": " > ".join([file_name] + display_path),
            "cmd":        node.get("cmd", ""),
            "note":       node.get("note", ""),
        })
        return
    for key, child in node.items():
        if isinstance(child, dict):
            _collect_entries(child, path + [key], file_name, out)


def _all_entries(data: dict[str, dict]) -> list[dict]:
    entries = []
    for file_name, file_data in data.items():
        for wrapper_key, subtree in file_data.items():
            if isinstance(subtree, dict):
                _collect_entries(subtree, [wrapper_key], file_name, entries)
    return entries


def _tree_node(node: dict, label: str, depth: int) -> None:
    """Recursively print a node. Leaf groups show command count."""
    indent = "  " + ("     " * depth)
    prefix = f"{GRAY}└─{RESET}"

    cmd_count   = sum(1 for v in node.values() if isinstance(v, dict) and "cmd" in v)
    branch_kids = {k: v for k, v in node.items()
                   if isinstance(v, dict) and "cmd" not in v}

    suffix    = f"  {GRAY}({cmd_count}){RESET}" if cmd_count else ""
    bold_open = BOLD if depth <= 1 else ""
    bold_cls  = RESET if depth <= 1 else ""
    print(f"{indent}{prefix} {bold_open}{label}{bold_cls}{suffix}")

    for child_key, child_node in branch_kids.items():
        _tree_node(child_node, child_key, depth + 1)


def _print_tree(data: dict[str, dict]) -> None:
    print(f"\n  {BOLD}Knowledge Base{RESET}\n")
    for file_name, file_data in data.items():
        print(f"  {CYAN}{file_name}{RESET}")
        for wrapper_key, subtree in file_data.items():
            if isinstance(subtree, dict):
                _tree_node(subtree, wrapper_key, depth=1)
    print()


def _search(keywords: list[str], data: dict[str, dict]) -> list[dict]:
    """Return entries where ALL keywords match anywhere in path+cmd+note."""
    kw = [k.lower() for k in keywords]
    results = []
    for e in _all_entries(data):
        searchable = " ".join(e["path"] + [e["file"], e["cmd"], e["note"]]).lower()
        if all(k in searchable for k in kw):
            results.append(e)
    return results


def _print_results(results: list[dict]) -> None:
    global _last_listed
    _last_listed = results
    _save_last(results)

    if not results:
        print(f"  {YELLOW}[!]{RESET} No results found")
        return

    current_bc = None
    for i, e in enumerate(results, 1):
        if e["breadcrumb"] != current_bc:
            current_bc = e["breadcrumb"]
            print(f"\n  {GRAY}{current_bc}{RESET}")
        preview = ""
        if e["note"]:
            short = e["note"][:65]
            preview = f"  {GRAY}# {short}{'...' if len(e['note']) > 65 else ''}{RESET}"
        print(f"  {CYAN}[{i}]{RESET}  {WHITE}{e['cmd']}{RESET}{preview}")
    print()


def _print_help(n: int) -> None:
    results = _last_listed or _load_last()
    if not results:
        print(f"  {RED}[!]{RESET} No commands listed yet — run a search first")
        return
    if n < 1 or n > len(results):
        print(f"  {RED}[!]{RESET} No command [{n}] — last search returned {len(results)} result(s)")
        return

    e = results[n - 1]
    print(f"\n  {GRAY}{e['breadcrumb']}{RESET}\n")

    print(f"  {BOLD}Command{RESET}")
    lines = e["cmd"].splitlines()
    if len(lines) > 1:
        print(f"  {DIM}┌{'─' * 60}{RESET}")
        for line in lines:
            print(f"  {DIM}│{RESET} {WHITE}{line}{RESET}")
        print(f"  {DIM}└{'─' * 60}{RESET}")
    else:
        print(f"  {WHITE}{e['cmd']}{RESET}")

    if e["note"]:
        print(f"\n  {BOLD}Notes{RESET}")
        for line in e["note"].split("\n"):
            if not line.strip():
                print()
                continue
            words = line.split()
            buf = []
            for word in words:
                buf.append(word)
                if len(" ".join(buf)) > 70:
                    print(f"  {GRAY}{' '.join(buf[:-1])}{RESET}")
                    buf = [word]
            if buf:
                print(f"  {GRAY}{' '.join(buf)}{RESET}")
    print()


def run(args: list[str]) -> None:
    data = _load_all()

    if not data:
        print(f"  {RED}[!]{RESET} No .json files found in {KB_DIR}")
        return

    if not args or args == ["list"]:
        _print_tree(data)
        return

    if "help" in args:
        idx = args.index("help")
        if idx + 1 < len(args) and args[idx + 1].isdigit():
            _print_help(int(args[idx + 1]))
        else:
       	    lines = [
            f"  {RED}[!]{RESET} Usage:",
            f"  {RED}[!]{RESET} kb                    show top-level tree",
            f"  {RED}[!]{RESET} kb help <N>           expanded view of command N from last search",
            f"  {RED}[!]{RESET} kb list               alias for no-args tree view"]
            print("\n".join(lines))
        return

    _print_results(_search(args, data))


def main() -> None:
    run(sys.argv[1:])


if __name__ == "__main__":
    main()
