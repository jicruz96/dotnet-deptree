import os
from typing import Any, Self

from dotnet_deptree.dag.dag import DAG, DAGNode

DEFAULT_NODE_ATTRS = {
    "style": "filled",
    "fillcolor": "cornflowerblue",
}


class PathDAGNode(DAGNode):

    sep = os.path.sep

    @property
    def basename(self) -> str:
        return self.name.split(self.sep)[-1]

    @property
    def label(self) -> str:
        x = self.data.get("label", self.basename)
        if "csproj" in x:
            breakpoint()
        return x


class PathDAG(DAG):
    node_class = PathDAGNode
    sep = os.path.sep

    def add(self, name: str, data: dict[str, Any]) -> PathDAGNode:
        node = super().add(name, data=data)
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
