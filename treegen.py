import os
import sys


def generate_tree(root_dir, prefix="", ignore_hidden=False):
    """Recursively generate a file tree as a list of strings."""
    lines = []
    try:
        entries = sorted(os.scandir(root_dir), key=lambda e: (not e.is_dir(), e.name.lower()))
    except PermissionError:
        return [prefix + "  [Permission Denied]"]

    if ignore_hidden:
        entries = [e for e in entries if not e.name.startswith(".")]

    for i, entry in enumerate(entries):
        is_last = i == len(entries) - 1
        connector = "└── " if is_last else "├── "
        lines.append(prefix + connector + entry.name + ("/" if entry.is_dir() else ""))
        if entry.is_dir():
            extension = "    " if is_last else "│   "
            lines.extend(generate_tree(entry.path, prefix + extension, ignore_hidden))

    return lines


def main():
    root_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    output_file = sys.argv[2] if len(sys.argv) > 2 else "tree.txt"
    ignore_hidden = "--no-hidden" in sys.argv

    if not os.path.isdir(root_dir):
        print(f"Error: '{root_dir}' is not a valid directory.")
        sys.exit(1)

    abs_path = os.path.abspath(root_dir)
    lines = [abs_path + "/"] + generate_tree(abs_path, ignore_hidden=ignore_hidden)
    output = "\n".join(lines) + "\n"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(output)

    print(f"Tree written to '{output_file}' ({len(lines)} lines)")
    print(output)


if __name__ == "__main__":
    main()