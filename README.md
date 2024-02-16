# .NET Dependency Tree Generator

## Install

### Requirements

* Poetry
* Python >= 3.11
* [`graphviz`](https://graphviz.org/download/)

1. Clone this repository
2. Run `poetry install`

## Usage

```
$ dotnet-deptree --help
usage: dotnet-deptree [-h] [--format {svg,png,pdf,dot}] [--exclude-projects]
                      [--exclude-packages] [--output OUTPUT] [--open]
                      project_paths [project_paths ...]

Generate dependency tree visualizations as for .NET projects.

Can be used to visualize package and project dependencies for a single project or a collection of projects.

positional arguments:
  project_paths         Generate dependency tree visualizations for one or
                        more .NET projects.

options:
  -h, --help            show this help message and exit
  --format {svg,png,pdf,dot}, -f {svg,png,pdf,dot}
                        The format of the rendered output. One of: svg, png,
                        pdf, dot. Default: svg.
  --exclude-projects    Exclude local project references from the dependency
                        tree.
  --exclude-packages    Exclude package references from the dependency tree.
  --output OUTPUT, -o OUTPUT
                        rendered output filename. prints to stdout by default
  --open                Open the generated files in the default web browser
```
