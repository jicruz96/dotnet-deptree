from __future__ import annotations

import glob
import os.path
from dataclasses import dataclass
from functools import cached_property
from typing import Any, Self

import xmltodict

from dotnet_deptree.dag.dag import DAG
from dotnet_deptree.dag.path_based_dependency_tree import PathTree, PathTreeNode


class DotNetDependencyNode(PathTreeNode):
    sep = "."


class DotNetPackageDependencyTree(PathTree):
    sep = "."
    node_class = DotNetDependencyNode


class DotNetProjectDependencyTree(DAG):
    node_class = DotNetDependencyNode


class DotNetCsprojParserError(Exception):
    pass


class DotNetProjectPath:
    def __init__(self, path: str):
        self.__path = self.validate_path(path)

    path = property(lambda s: s.__path)
    name = property(lambda s: os.path.basename(s.path))
    csproj_path = property(lambda s: os.path.join(s.path, f"{s.name}.csproj"))
    sln_path = property(lambda s: os.path.join(s.path, f"{s.name}.sln"))
    project_name = property(lambda s: s.name.split(".")[0])
    module_name = property(lambda s: s.name.split(".", maxsplit=1)[-1])

    @classmethod
    def eval(cls, path: str | Self) -> Self:
        if isinstance(path, cls):
            return path
        if isinstance(path, str):
            return cls(path)
        TypeError(f"Expected str or {cls.__name__}, got {path} of type {type(path)}.")

    @staticmethod
    def validate_path(path: str) -> str:

        invalid_path_help = (
            "Please provide a valid "
            "path to a .sln or .csproj file or to a directory containing one "
            "of those (note: the directory name must match the name of the "
            ".csproj/.sln file)."
        )

        if not os.path.exists(path):
            raise FileNotFoundError(f"No file or directory found at {path}. {invalid_path_help}")
        basename = os.path.basename(path)
        if not os.path.isdir(path):
            if not path.endswith(".csproj"):
                raise ValueError(f"{path} is not a .csproj file. {invalid_path_help}")
            dirname = os.path.dirname(path)
            parent_dir = dirname.split(os.path.sep)[-1]
            if not basename.startswith(parent_dir):
                raise ValueError(
                    f"File {path} does not match the directory name. {invalid_path_help}"
                )
            return dirname
        csproj = os.path.join(path, f"{basename}.csproj")
        sln = os.path.join(path, f"{basename}.sln")
        if not os.path.exists(csproj) and not os.path.exists(sln):
            raise ValueError(f"No .csproj or .sln file found at {csproj}. {invalid_path_help}")
        return path


class DotNetProjectModule:

    path: DotNetProjectPath
    csproj: dict[str, Any]

    def __init__(self, path: str | DotNetProjectPath) -> None:
        self.path = DotNetProjectPath.eval(path)
        try:
            with open(self.path.csproj_path) as f:
                self.csproj = xmltodict.parse(f.read())
        except Exception as e:
            raise DotNetCsprojParserError(
                f"Error parsing .csproj file at {self.path.csproj_path}: {e}"
            ) from e

    @cached_property
    def project_dependency_tree(self) -> DotNetProjectDependencyTree:
        tree = DotNetProjectDependencyTree()
        for ref in self._get_items_from_csproj("ProjectReference"):
            relative_path = ref["@Include"].replace("\\", os.path.sep)
            project_path_str = os.path.join(self.path.path, relative_path)
            path = DotNetProjectPath.eval(project_path_str)
            node_data = {
                "name": path.name,
                "project_name": path.project_name,
                "module_name": path.module_name,
                "is_project": True,
            }
            tree.add(path.name, data=node_data)

        # add the project itself as a node
        project_node = tree.get_or_add(self.path.name)
        # make all project references a parent of the project node
        for node in tree.all():
            if node is not project_node:
                node.add_child(project_node)
        return tree

    @cached_property
    def package_dependency_tree(self) -> DotNetPackageDependencyTree:
        return DotNetPackageDependencyTree(
            nodes_data=[
                {"name": ref["@Include"]} for ref in self._get_items_from_csproj("PackageReference")
            ],
        )

    @cached_property
    def modules(self) -> list[Self]:
        modules = []
        for subdir in glob.glob(os.path.join(self.path.path, "*/")):
            subdirpath = os.path.join(self.path.path, subdir)
            for module_path in _get_child_project_paths(subdirpath):
                module = self.__class__(module_path)
                modules.append(module)
        return modules

    def _get_items_from_csproj(self, item: str) -> list[dict[str, str]]:
        items_list = []
        item_groups = self.csproj["Project"].get("ItemGroup", [])
        if isinstance(item_groups, dict):
            item_groups = [item_groups]
        for item_group in item_groups:
            items = item_group.get(item)
            if not items:
                continue
            if isinstance(items, dict):
                items = [items]
            items_list.extend(items)
        return items_list


@dataclass
class DotNetProject:
    path: DotNetProjectPath
    modules: list[DotNetProjectModule]

    @property
    def project_name(self) -> str:
        return self.path.project_name

    @classmethod
    def from_path(cls, path: str | DotNetProjectPath) -> DotNetProject:
        """Create a DotNetProject, provided a path to a .NET project directory."""
        if isinstance(path, DotNetProjectPath):
            pathobj = path
        elif isinstance(path, str):
            pathobj = DotNetProjectPath(os.path.abspath(path))
        else:
            raise TypeError(f"Expected str or {DotNetProjectPath.__name__}, got {path}.")
        modules = []
        for child_proj_path in _get_child_project_paths(pathobj.path):
            modules.append(DotNetProjectModule(child_proj_path))
        return cls(path=pathobj, modules=modules)


def _get_child_project_paths(path: str) -> list[str]:
    """Recursively find all child project paths in a directory, but not
    any grandchild projects.
    """
    if not os.path.isdir(path):
        raise ValueError(f"Path {path} is not a directory.")
    csproj = os.path.join(path, f"{os.path.basename(path)}.csproj")
    if os.path.exists(csproj):
        return [path]
    paths = []
    for subdir in glob.glob(os.path.join(path, "*/")):
        # strip trailing slash
        subdir = subdir[:-1]
        for subdirpath in _get_child_project_paths(subdir):
            paths.append(subdirpath)
    return paths
