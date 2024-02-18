from __future__ import annotations

import argparse

from dotnet_deptree.deptree_generator import DotNetProjectsDependencyTreeGenerator
from dotnet_deptree.dotnet import DotNetProject


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Generate dependency tree visualizations as for .NET projects\n\n"
            "Can be used to visualize package and project dependencies for a "
            "single project or a collection of projects."
        ),
    )
    parser.add_argument(
        "project_paths",
        nargs="+",
        help="Generate dependency tree visualizations for one or more .NET projects.",
    )
    parser.add_argument(
        "--format",
        "-f",
        choices=DotNetProjectsDependencyTreeGenerator.formats,
        default=DotNetProjectsDependencyTreeGenerator.default_format,
        help=(
            "The format of the rendered output. One of: "
            f"{', '.join(DotNetProjectsDependencyTreeGenerator.formats)}. "
            f"Default: {DotNetProjectsDependencyTreeGenerator.default_format}."
        ),
    )
    parser.add_argument(
        "--exclude-projects",
        action="store_true",
        help="Exclude local project references from the dependency tree.",
    )
    parser.add_argument(
        "--exclude-packages",
        action="store_true",
        help="Exclude package references from the dependency tree.",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="rendered output filename. prints to stdout by default",
    )
    parser.add_argument(
        "--open",
        action="store_true",
        help="Open the generated files in the default web browser",
    )
    args = parser.parse_args()
    projects = []
    for path in args.project_paths:
        project = DotNetProject.from_path(path)
        projects.append(project)
    dtg = DotNetProjectsDependencyTreeGenerator(
        projects=projects,
        output_filename=args.output,
        exclude_projects=args.exclude_projects,
        exclude_packages=args.exclude_packages,
        open_on_render=args.open,
        format=args.format,
    )
    dtg.create_dependency_tree()


if __name__ == "__main__":
    main()
