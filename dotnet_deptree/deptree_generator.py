from __future__ import annotations

import os.path
import tempfile
from typing import Literal, Optional

import graphviz

from dotnet_deptree.dag.path_based_dependency_tree import PathTreeNode
from dotnet_deptree.dotnet import (
    DotNetPackageDependencyTree,
    DotNetProject,
    DotNetProjectDependencyTree,
)

FormatType = Literal["svg", "png", "pdf", "dot"]

COLOR_PALETTE = [
    "#B9E6FF",
    "#51A7AD",
    "#F1EDE3",
    "#DCD2D8",
    "#5EFC8D",
    "#F5B700",
    "#FFA9A3",
    "#5C95FF",
]
DEFAULT_COLOR = COLOR_PALETTE[0]


class DotNetProjectsDependencyTreeGenerator:

    formats = list(FormatType.__args__)  # type: ignore
    default_format = "svg"

    def __init__(
        self,
        projects: list[DotNetProject],
        format: FormatType,
        output_filename: Optional[str] = None,
        exclude_projects: bool = False,
        exclude_packages: bool = False,
        open_on_render: bool = False,
    ):
        if exclude_projects and exclude_packages:
            raise ValueError(
                "Cannot exclude both project and package dependencies. "
                "Please specify at least one type of dependency to include."
            )
        if open_on_render and not output_filename:
            raise ValueError(
                "Cannot open the rendered file without specifying an output "
                "filename."
            )
        self.projects = projects
        self.output_filename = output_filename
        self.exclude_projects = exclude_projects
        self.exclude_packages = exclude_packages
        self.open_on_render = open_on_render
        self.format: FormatType = format

    def create_dependency_tree(self):
        graph = self.create_dependency_graph()
        self.render_graph(
            graph=graph,
            format=self.format,
            stagger=10,
            view=self.open_on_render,
        )

    def create_dependency_graph(self) -> graphviz.Digraph:
        if self.exclude_projects and self.exclude_packages:
            raise NotImplementedError()
        tree = self._create_package_dependency_tree()
        tree = self._create_project_dependency_tree(tree)
        graph = tree.to_graphviz(
            merge_single_path_nodes=False,
            style=self.generate_node_style,  # type: ignore
        )
        return graph

    def _create_package_dependency_tree(self) -> DotNetProjectDependencyTree:
        if self.exclude_packages:
            return DotNetProjectDependencyTree()
        tree = DotNetPackageDependencyTree()
        for project in self.projects:
            for module in project.modules:
                module_tree = module.package_dependency_tree
                if not self.exclude_projects:
                    for node in module_tree.all():
                        node.data["parent_module"] = module.path.name
                tree = tree.merge(module_tree)
        tree = tree.compress()
        tree = DotNetProjectDependencyTree().merge(tree)  # type: ignore
        for node in tree.all():
            parent_module_name = node.data.get("parent_module")
            if parent_module_name:
                node.add_child(tree.get_or_add(parent_module_name))
            node.data.update(
                {
                    "is_package": not self.is_known_project_name(node.name),
                    "label": node.name if node.is_root else node.basename,  # type: ignore  # noqa: E501
                }
            )
        return tree

    def _create_project_dependency_tree(
        self, tree: DotNetProjectDependencyTree
    ) -> DotNetProjectDependencyTree:
        if self.exclude_projects:
            return tree

        for project in self.projects:
            for module in project.modules:
                tree = tree.merge(module.project_dependency_tree)
                module_node = tree.get(module.path.name)
                package_tree = module.package_dependency_tree.compress()
                for package_node in package_tree.all():
                    is_project = self.is_known_project_name(package_node.name)
                    connected_to_module_node = (
                        package_node.name in tree.all_names
                        and module_node.is_descendant_of(tree.get(package_node.name))
                    )
                    if is_project and not connected_to_module_node:
                        new_node = tree.get_or_add(package_node.name)
                        new_node.data.update(package_node.data)
                        new_node.add_child(module_node)
        return tree

    def render_graph(
        self,
        graph: graphviz.Digraph,
        format: FormatType,
        stagger: int = 1,
        view: bool = False,
    ):
        def _render(outfile: str):
            g = graph.unflatten(stagger=stagger, fanout=True, chain=1000)
            g.render(outfile=outfile, format=format, cleanup=True, view=view)

        if self.output_filename:
            _render(self.output_filename)
            return
        try:
            tf = tempfile.NamedTemporaryFile(delete=False, suffix=f".{format}")
            _render(tf.name)
            tf.seek(0)
            print(tf.read().decode("utf-8"))
            tf.close()
        finally:
            os.unlink(tf.name)

    @staticmethod
    def generate_node_style(node: PathTreeNode) -> dict[str, str]:
        attrs = {
            # use larger, bolder text if node is a root
            "fontsize": "8",
            "fontname": "Courier New",
            "fillcolor": DEFAULT_COLOR,
            "style": "filled",
        }
        if node.data.get("is_package"):
            attrs["fillcolor"] = "#FFA07A"
            attrs["href"] = f"https://www.nuget.org/packages/{node.name}"

            # attrs.update(node.data)
            if node.data.get("parent_module"):
                attrs["label"] = node.name
            elif "label" in node.data:
                attrs["label"] = node.data["label"]
            else:
                attrs["label"] = node.basename
        return attrs

    def is_known_project_name(self, name: str) -> bool:
        return any(name.startswith(p.project_name) for p in self.projects)
