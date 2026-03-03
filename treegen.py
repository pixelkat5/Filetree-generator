import argparse
import os
import sys


def format_size(size_bytes):
    """Format a byte count into a human-readable string."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}" if unit != "B" else f"{size_bytes} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} PB"


def summarize_dir(path, ignore_hidden=False):
    """Recursively count files, directories, and total size under a path."""
    file_count = 0
    dir_count = 0
    total_size = 0
    try:
        entries = os.scandir(path)
    except PermissionError:
        return 0, 0, 0
    for entry in entries:
        if ignore_hidden and entry.name.startswith("."):
            continue
        if entry.is_dir(follow_symlinks=False):
            dir_count += 1
            sub_files, sub_dirs, sub_size = summarize_dir(entry.path, ignore_hidden)
            file_count += sub_files
            dir_count += sub_dirs
            total_size += sub_size
        else:
            file_count += 1
            try:
                total_size += entry.stat(follow_symlinks=False).st_size
            except OSError:
                pass
    return file_count, dir_count, total_size


def _dir_summary_label(sub_files, sub_dirs, sub_size):
    """Build an inline summary string for a directory."""
    parts = []
    if sub_dirs:
        parts.append(f"{sub_dirs} dir{'s' if sub_dirs != 1 else ''}")
    if sub_files:
        parts.append(f"{sub_files} file{'s' if sub_files != 1 else ''}")
    parts.append(format_size(sub_size))
    return f" ({', '.join(parts)})"


def generate_tree(root_dir, prefix="", ignore_hidden=False, max_depth=None, verbose=False, _current_depth=0):
    """Recursively generate a file tree as a list of strings.

    Returns:
        tuple: (lines, file_count, dir_count, total_size)
    """
    lines = []
    file_count = 0
    dir_count = 0
    total_size = 0

    try:
        entries = sorted(os.scandir(root_dir), key=lambda e: (not e.is_dir(), e.name.lower()))
    except PermissionError:
        return [prefix + "  [Permission Denied]"], 0, 0, 0

    if ignore_hidden:
        entries = [e for e in entries if not e.name.startswith(".")]

    for i, entry in enumerate(entries):
        is_last = i == len(entries) - 1
        connector = "└── " if is_last else "├── "
        lines.append(prefix + connector + entry.name + ("/" if entry.is_dir() else ""))

        if entry.is_dir():
            dir_count += 1
            if max_depth is not None and _current_depth >= max_depth:
                sub_files, sub_dirs, sub_size = summarize_dir(entry.path, ignore_hidden)
                file_count += sub_files
                dir_count += sub_dirs
                total_size += sub_size
                if verbose:
                    lines[-1] += _dir_summary_label(sub_files, sub_dirs, sub_size)
            else:
                extension = "    " if is_last else "│   "
                sub_lines, sub_files, sub_dirs, sub_size = generate_tree(
                    entry.path, prefix + extension, ignore_hidden, max_depth, verbose, _current_depth + 1
                )
                lines.extend(sub_lines)
                file_count += sub_files
                dir_count += sub_dirs
                total_size += sub_size
                if verbose:
                    lines[-(len(sub_lines) + 1)] += _dir_summary_label(sub_files, sub_dirs, sub_size)
        else:
            file_count += 1
            try:
                total_size += entry.stat(follow_symlinks=False).st_size
            except OSError:
                pass

    return lines, file_count, dir_count, total_size


def build_summary(file_count, dir_count, total_size):
    """Build a summary line with counts and total size."""
    return (
        f"\n{dir_count} director{'y' if dir_count == 1 else 'ies'}, "
        f"{file_count} file{'s' if file_count != 1 else ''}, "
        f"{format_size(total_size)}"
    )


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate a visual directory tree."
    )
    parser.add_argument(
        "root_dir", nargs="?", default=".",
        help="Root directory to scan (default: current directory)"
    )
    parser.add_argument(
        "-o", "--output",
        help="Write tree to this file (in addition to stdout)"
    )
    parser.add_argument(
        "-d", "--max-depth", type=int, default=None,
        help="Maximum depth of recursion (0 = root contents only)"
    )
    parser.add_argument(
        "--no-hidden", action="store_true",
        help="Exclude hidden files and directories"
    )
    parser.add_argument(
        "--no-summary", action="store_true",
        help="Omit the file/directory count summary"
    )
    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Show inline file count and size summary for each directory"
    )
    return parser.parse_args()


def main():
    args = parse_args()

    if not os.path.isdir(args.root_dir):
        print(f"Error: '{args.root_dir}' is not a valid directory.")
        sys.exit(1)

    abs_path = os.path.abspath(args.root_dir)
    tree_lines, file_count, dir_count, total_size = generate_tree(
        abs_path, ignore_hidden=args.no_hidden, max_depth=args.max_depth, verbose=args.verbose
    )

    lines = [abs_path + "/"] + tree_lines
    output = "\n".join(lines)

    if not args.no_summary:
        output += build_summary(file_count, dir_count, total_size)

    output += "\n"

    print(output, end="")

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"\nTree written to '{args.output}' ({len(lines)} lines)")


if __name__ == "__main__":
    main()