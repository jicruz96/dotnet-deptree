# .NET Dependency Tree Generator

Create dependency tree visualizations for .NET projects. 

## Features

* Generate dependency tree visualizations for one or more .NET projects.
* Supports rendering to SVG, PNG, PDF, and DOT formats.
* Visualize your local project dependencies alone, your package dependencies alone, or both together.

## Install

```bash
pip install dotnet-deptree
```

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

## Contributing

Visit the [GitHub repository](https://github.com/jicruz96/dotnet-deptree) for the latest source code.

### Requirements

* Poetry
* Python >= 3.11
* [`graphviz`](https://graphviz.org/download/)

1. Clone this repository
2. Run `poetry install`
