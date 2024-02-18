"""Implementation of a "Path-based" tree structure, which is a type of
Directed Acyclic Graph (DAG).
"""

import os
from typing import Any, Self

from dotnet_deptree.dag.dag import DAG, DAGNode

DEFAULT_NODE_ATTRS = {
    "style": "filled",
    "fillcolor": "cornflowerblue",
}


class PathTreeNode(DAGNode):
    """A node in a PathTree.

    See PathTree for more information.
    """

    sep = os.path.sep

    @property
    def basename(self) -> str:
        return self.name.split(self.sep)[-1]

    @property
    def label(self) -> str:
        return self.data.get("label", self.basename)


class PathTree(DAG):
    """Utility to convert a list of file paths into a tree-like structure.

    For example, the following files:
        - a
        - a/b
        - a/b/1
        - a/b/2
        - a/c

    Would be represented as:
    ```
    PathTree
    ├── PathTreeNode(a)
    │   ├── PathTreeNode(a/b)
    │   │   ├── PathTreeNode(a/b/1)
    │   │   └── PathTreeNode(a/b/2)
    │   └── PathTreeNode(a/c)
    ```

    The tree can be visualized using the `to_graphviz` method, which will
    return a graphviz.Digraph object.

    Usage:
    ```python
    tree = PathTree()
    tree.add("a/b/1")
    tree.add("a/b/2")
    tree.add("a/c")
    tree.add("a")
    tree.add("d/e/f")
    tree.to_graphviz().render("tree")
    ```
    """

    node_class = PathTreeNode
    sep = os.path.sep

    def add(self, name: str, data: dict[str, Any] | None = None) -> PathTreeNode:
        node = super().add(name, data=(data or {}))
        if self.sep in name:
            parent = self.get_or_add(name.rsplit(self.sep, 1)[0])
            parent.add_child(node)
        return node  # type: ignore

    def copy(self) -> Self:
        new_dag = self.__class__()

        def _add_node(node: DAGNode) -> DAGNode:
            if node.name in new_dag.all_names:
                return new_dag.get(node.name)
            new_node = new_dag.add(node.name, data=node.data)
            new_node.data = node.data
            for child in map(_add_node, node.children):
                if not new_node.is_parent_of(child):  # type: ignore
                    new_node.add_child(child)  # type: ignore
            return new_node

        for node in self.roots():
            _add_node(node)
        return new_dag

    def merge(self, other: Self) -> Self:
        new_dag = self.copy()
        queue = other.roots()
        while queue:
            other_node = queue.pop(0)
            if other_node.name not in new_dag.all_names:
                node = new_dag.add(other_node.name, data=other_node.data)
            else:
                node = new_dag.get(other_node.name)
            node.data.update(other_node.data)
            queue.extend(other_node.direct_children)

        other_names = other.all_names
        for node in new_dag.all():
            if node.name not in other_names:
                continue
            other_node = other.get(node.name)
            for child in other_node.children:
                new_child = new_dag.get(child.name)
                if not node.is_parent_of(new_child):
                    node.add_child(new_child)
        return new_dag
