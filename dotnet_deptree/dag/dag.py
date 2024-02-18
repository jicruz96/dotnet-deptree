"""
Simple implementation of a directed acyclic graph (DAG) in Python.

This is not necessarily the most efficient implementation, but it is simple
enough for my purposes.
"""

from typing import Any, Callable, Self, Sequence

import graphviz

DEFAULT_NODE_STYLE = {
    "style": "filled",
    "fillcolor": "cornflowerblue",
}


class DAGNode:

    def __init__(self, name: str, data: dict[str, Any] | None = None):
        self.validate_data(data)
        self.name = name
        self.data = data or {}
        self.__children: list[Self] = []
        self.__parents: list[Self] = []

    def validate_data(self, data: dict[str, Any] | None) -> None:
        pass

    @property
    def children(self) -> list[Self]:
        return self.__children.copy()

    @property
    def parents(self) -> list[Self]:
        return self.__parents.copy()

    @property
    def direct_parents(self) -> list[Self]:
        return [
            parent
            for parent in self.__parents
            if not any(parent.is_ancestor_of(other) for other in self.__parents)
        ]

    @property
    def direct_children(self) -> list[Self]:
        return [
            child
            for child in self.__children
            if not any(child.is_descendant_of(other) for other in self.__children)
        ]

    def add_child(self, child: Self):
        if child is self:
            raise ValueError(f"{child.name} cannot be its own ancestor")
        if child.is_ancestor_of(self):
            raise ValueError(f"{self.name} is already a descendant of {child!r}")
        if self.is_parent_of(child):
            raise ValueError(f"{child} is already a child of {self!r}")
        self.__children.append(child)
        child.unsafely_add_parent_to_parents_array(self)

    def unsafely_add_child_to_children_array(self, child: Self):
        self.__children.append(child)

    def unsafely_add_parent_to_parents_array(self, parent: Self):
        self.__parents.append(parent)

    def unsafely_remove_child_from_children_array(self, child: Self):
        self.__children.remove(child)

    def unsafely_remove_parent_from_parents_array(self, parent: Self):
        self.__parents.remove(parent)

    def is_ancestor_of(self, node: Self) -> bool:
        for child in self.__children:
            if node is child or child.is_ancestor_of(node):
                return True
        return False

    def is_descendant_of(self, node: Self) -> bool:
        for parent in self.__parents:
            if node is parent or parent.is_descendant_of(node):
                return True
        return False

    def is_child_of(self, node: Self) -> bool:
        return node in self.__parents

    def is_parent_of(self, node: Self) -> bool:
        return node in self.__children

    @property
    def is_root(self) -> bool:
        return not self.__parents

    @property
    def is_leaf(self) -> bool:
        return not self.__children

    @property
    def roots(self) -> set[Self]:
        if not self.__parents:
            return {self}
        return {p for parent in self.__parents for p in parent.roots}

    def __repr__(self):
        return f"{self.label}({','.join([x.name for x in self.__children])})"

    @property
    def label(self) -> str:
        return self.data.get("label", self.name)


class DAG:
    node_class = DAGNode

    def __init__(self, nodes_data: Sequence[dict[str, Any]] | None = None):
        self.__nodes = {}
        if not nodes_data:
            return
        for node in nodes_data:
            if "name" not in node:
                raise ValueError("Expected 'name' key in node dictionary")
            self.add(node["name"], data=node)

    def add(self, name: str, data: dict[str, Any] | None = None) -> DAGNode:
        if name in self.__nodes:
            raise ValueError(f"Node with name {name!r} already exists")
        node = self.node_class(name, data=data)
        self.__nodes[name] = node
        return node

    def get(self, name: str) -> DAGNode:
        assert isinstance(name, str)
        return self.__nodes[name]

    def get_or_add(self, name: str) -> DAGNode:
        assert isinstance(name, str)
        if name in self.__nodes:
            return self.__nodes[name]
        return self.add(name)

    def all(self) -> list[DAGNode]:
        return list(set(self.__nodes.values()))

    def roots(self) -> list[DAGNode]:
        return [node for node in self.all() if not node.parents]

    def leaves(self) -> list[DAGNode]:
        return [node for node in self.all() if not node.children]

    def remove(self, name_or_node: str | DAGNode) -> Self:
        if isinstance(name_or_node, DAGNode):
            node = name_or_node
            if node not in self.__nodes.values():
                raise ValueError(f"{node} is not part of this DAG")
        elif isinstance(name_or_node, str):
            if name_or_node not in self.__nodes:
                raise ValueError(f"No node with name {name_or_node!r}")
            node = self.__nodes[name_or_node]
        else:
            raise TypeError(
                f"Expected str or DAGNode, got {name_or_node} of type "
                f"{type(name_or_node).__name__}"
            )
        # remove node reference from parents
        for parent in node.parents:
            parent.unsafely_remove_child_from_children_array(node)
        # remove node reference from children
        for child in node.children:
            child.unsafely_remove_parent_from_parents_array(node)
        # add children to parents
        for parent in node.parents:
            for child in node.children:
                if not parent.is_ancestor_of(child):
                    parent.add_child(child)
        return self.__nodes.pop(node.name)

    def compress(self) -> Self:
        """Merge nodes that are part of a single path into a single node."""
        tree = self.copy()
        queue = tree.leaves()
        while queue:
            node = queue.pop(0)
            parents_with_single_child = [
                parent for parent in node.parents if len(parent.children) == 1
            ]
            if len(parents_with_single_child) == 1:
                parent = parents_with_single_child[0]
                tree.remove(parent)
                if parent in queue:
                    queue.remove(parent)
                assert parent.children[0] is node
                for key, value in parent.data.items():
                    if key == "label" and "label" in node.data:
                        node.data["label"] = f"{value} -> {node.data['label']}"
                    else:
                        node.data[key] = value
                tree.__nodes[parent.name] = node
                queue.append(node)
            queue.extend(node.direct_parents)
        return tree

    def to_graphviz(
        self,
        merge_single_path_nodes: bool = True,
        style: (
            dict[str, str] | str | Callable[[DAGNode], dict[str, str]]
        ) = DEFAULT_NODE_STYLE,
    ) -> graphviz.Digraph:
        tree = self.copy()
        if merge_single_path_nodes:
            tree = tree.compress()
        if callable(style):
            styler = style
        elif isinstance(style, dict):
            styler = lambda _: style
        elif isinstance(style, str):
            styler = lambda node: node.data.get(style, {})
        else:
            raise TypeError(
                f"Expected dict, str, or callable, got {style} of type "
                f"{type(style).__name__}"
            )
        graph = graphviz.Digraph()
        queue = tree.leaves()
        seen = set()
        while queue:
            node = queue.pop(0)
            attrs = styler(node)
            graph.node(name=attrs.pop("name", node.name), **attrs)
            for parent in node.direct_parents:
                graph.edge(parent.name, node.name)
                if parent not in seen:
                    queue.append(parent)
                    seen.add(parent)
        return graph

    def copy(self) -> Self:
        new_dag = self.__class__()

        def _add_node(node: DAGNode) -> DAGNode:
            if node.name in new_dag.all_names:
                return new_dag.get(node.name)
            new_node = new_dag.add(node.name, data=node.data)
            new_node.data = node.data
            for child in map(_add_node, node.children):
                if not new_node.is_parent_of(child):
                    new_node.add_child(child)
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
            for other_child in other_node.direct_children:
                if other_child.name not in self.all_names:
                    queue.append(other_child)

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

    @property
    def all_names(self) -> set[str]:
        return set(self.__nodes.keys())
