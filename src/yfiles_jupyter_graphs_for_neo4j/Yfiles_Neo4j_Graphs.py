"""Jupyter (ipy)widget powered by yFiles.

The main Neo4jGraphWidget class is defined in this module.

"""
import warnings
from typing import Any, Callable, Dict, Union, Type, Optional, List
from yfiles_jupyter_graphs import GraphWidget

# TODO maybe change to get dynamically when adding bindings

POSSIBLE_NODE_BINDINGS = {"coordinate", "color", "size", "type", "styles", "scale_factor", "position",
                          "layout", "property", "label"}
POSSIBLE_EDGE_BINDINGS = {"color", "thickness_factor", "styles", "property", "label"}
NEO4J_LABEL_KEYS = ["name", "title", "text", "description", "caption", "label"]

class Neo4jGraphWidget:
    """
    A yFiles Graphs for Jupyter widget that is tailored to visualize Cypher queries resolved against a Neo4j database.
    """

    # noinspection PyShadowingBuiltins
    def __init__(self, driver: Optional[Any] = None, widget_layout: Optional[Any] = None,
                 overview_enabled: Optional[bool] = None, context_start_with: Optional[str] = None,
                 license: Optional[Dict] = None,
                 autocomplete_relationships: Optional[bool] = False, layout: Optional[str] = "organic"):
        """
        Initializes a new instance of the Neo4jGraphWidget class.

        Args:
            driver (Optional[neo4j._sync.driver.Neo4jDriver]): The Neo4j driver to resolve the Cypher queries.
            widget_layout (Optional[ipywidgets.Layout]): Can be used to specify general widget appearance through css attributes.
                See ipywidgets documentation for the available keywords.
            overview_enabled (Optional[bool]): Whether the graph overview is enabled or not.
            context_start_with (Optional[str]): Start with a specific side-panel opened in the interactive widget. Starts with closed side-panel by default.
            license (Optional[Dict]): The widget works on common public domains without a specific license.
                For unknown domains, a license can be obtained by the creators of the widget.
            autocomplete_relationships (Optional[bool]): Whether missing relationships in the Cypher's return value are automatically added.
            layout (Optional[str]): Specifies the default automatic graph arrangement. Can be overwritten for each
                cypher separately. By default, an "organic" layout is used. Supported values are:
                    - "circular"
                    - "circular_straight_line"
                    - "hierarchic"
                    - "organic"
                    - "interactive_organic"
                    - "orthogonal"
                    - "radial"
                    - "tree"
                    - "map"
                    - "orthogonal_edge_router"
                    - "organic_edge_router"
        """

        self._widget = GraphWidget()
        self.driver = driver
        self._license = license
        self._overview = overview_enabled
        self._layout = widget_layout
        self._context_start_with = context_start_with
        self.autocomplete_relationships = autocomplete_relationships
        self._graph_layout = layout

        self._node_configurations = {}
        self._edge_configurations = {}
        self._parent_configurations = set()

    # region driver

    @property
    def driver(self) -> Any:
        """The Neo4j driver that is used to resolve the Cypher queries."""
        return self._driver

    @driver.setter
    def driver(self, driver: Any) -> None:
        """
        The Neo4j driver that is used to resolve the Cypher queries. A new session is created when set.

        Args:
            driver (neo4j._sync.driver.Neo4jDriver): The Neo4j driver to resolve the Cypher queries.

        Returns:
            None
        """
        self._driver = driver
        self._session = driver.session()

    def set_driver(self, driver: Any) -> None:
        """Legacy setter for the driver property.

        Deprecated, use ``widget.driver = value`` instead.
        """
        warnings.warn(
            "set_driver() is deprecated; use `widget.driver = value` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        self.driver = driver

    def get_driver(self) -> Any:
        """Legacy getter for the driver property.

        Deprecated, use ``widget.driver`` instead.
        """
        warnings.warn(
            "get_driver() is deprecated; use `widget.driver` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.driver

    # endregion

    # region autocomplete_relationships

    @property
    def autocomplete_relationships(self) -> Union[bool, list[str]]:
        """Whether relationship autocompletion is enabled for all or specific relationship types."""
        return self._autocomplete_relationships

    @autocomplete_relationships.setter
    def autocomplete_relationships(self, autocomplete_relationships: Union[bool, str, list[str]]) -> None:
        """
        Sets the flag to enable or disable autocomplete for relationships.
        When autocomplete is enabled, relationships are automatically completed in the graph,
        similar to the behavior in Neo4j Browser.
        This can be set to True/False to enable or disable for all relationships,
        or a single relationship type or a list of relationship types to enable for specific relationships.

        Args:
            autocomplete_relationships (Union[bool, str, list[str]]): Enable autocompletion for relationships
                in general, or for a single type, or for multiple types.

        Returns:
            None
        """
        if not isinstance(autocomplete_relationships, (bool, str, list)):
            raise ValueError("autocomplete_relationships must be a bool, a string, or a list of strings")
        if isinstance(autocomplete_relationships, str):
            self._autocomplete_relationships = [autocomplete_relationships]
        else:
            self._autocomplete_relationships = autocomplete_relationships

    def set_autocomplete_relationships(self, autocomplete_relationships: Union[bool, str, list[str]]) -> None:
        """Legacy setter for the autocomplete relationships property.

        Deprecated, use ``widget.autocomplete_relationships = value`` instead.
        """
        warnings.warn(
            "set_autocomplete_relationships() is deprecated; use `widget.autocomplete_relationships = value` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        self.autocomplete_relationships = autocomplete_relationships

    # endregion

    def _is_autocomplete_enabled(self) -> bool:
        if isinstance(self._autocomplete_relationships, bool):
            return self._autocomplete_relationships
        return len(self._autocomplete_relationships) > 0

    def _get_relationship_types_expression(self) -> str:
        if isinstance(self._autocomplete_relationships, list) and len(self._autocomplete_relationships) > 0:
            return "AND type(rel) IN $relationship_types"
        return ""

    def show_cypher(self, cypher: str, layout: Optional[str] = None, **kwargs: Any) -> None:
        """
        Displays the given Cypher query as interactive graph.

        Args:
            cypher (str): The Cypher query whose result should be visualized as graph.
            layout (Optional[str]): The graph layout for this request. Overwrites the general default `layout` that was
                specified when initializing the class. Supported values are:
                    - "circular"
                    - "circular_straight_line"
                    - "hierarchical"
                    - "organic"
                    - "interactive_organic"
                    - "orthogonal"
                    - "radial"
                    - "tree"
                    - "map"
                    - "orthogonal_edge_router"
                    - "organic_edge_router"
            **kwargs (Any): Additional parameters that should be passed to the Cypher query.

        Returns:
            None

        Raises:
            Exception: If no driver was specified.
        """
        if self._driver is not None:
            if self._is_autocomplete_enabled():
                nodes = self._session.run(cypher, **kwargs).graph().nodes
                node_ids = [Neo4jGraphWidget.__get_neo4j_element_id(node) for node in nodes]
                reltypes_expr = self._get_relationship_types_expression()
                cypher = f"""
                    MATCH (n) WHERE elementId(n) IN $node_ids
                    RETURN n as start, NULL as rel, NULL as end
                    UNION ALL
                    MATCH (n)-[rel]-(m)
                    WHERE elementId(n) IN $node_ids
                    AND elementId(m) IN $node_ids
                    {reltypes_expr}
                    RETURN n as start, rel, m as end
                """
                kwargs = {"node_ids": node_ids}
                if reltypes_expr:
                    kwargs["relationship_types"] = self._autocomplete_relationships
            graph = self._session.run(cypher, **kwargs).graph()
            widget = GraphWidget(overview_enabled=self._overview, context_start_with=self._context_start_with,
                                 widget_layout=self._layout, license=self._license,
                                 graph=graph)
            self.__remember_neo4j_element_ids(widget, graph)
            self.__create_group_nodes(self._node_configurations, widget)
            self.__apply_node_mappings(widget)
            self.__apply_edge_mappings(widget)
            self.__apply_heat_mapping({**self._node_configurations, **self._edge_configurations}, widget)
            self.__apply_parent_mapping(widget)
            if layout is None:
                widget.graph_layout = self._graph_layout
            else:
                widget.graph_layout = layout

            widget.node_cell_mapping = self.node_cell_mapping

            self._widget = widget
            widget.show()
        else:
            raise Exception("no driver specified")

    @staticmethod
    def __get_neo4j_element_id(element: Any) -> Any:
        """Get the stable Neo4j element ID, with a fallback for older drivers."""
        element_id = getattr(element, "element_id", None)
        if element_id is not None:
            return element_id
        return element.id

    @staticmethod
    def __remember_neo4j_element_ids(widget: GraphWidget, graph: Any) -> None:
        """Keep Neo4j element IDs alongside the core widget's internal graph IDs.

        yFiles Graphs for Jupyter currently uses ``Node.id`` and ``Relationship.id``
        as its graph keys. Those IDs are not the values expected by Cypher's
        ``elementId`` function, so selection helpers need a mapping back to the
        original Neo4j entities.
        """
        setattr(widget, "_neo4j_node_element_ids", {
            node.id: Neo4jGraphWidget.__get_neo4j_element_id(node)
            for node in graph.nodes
        })
        setattr(widget, "_neo4j_relationship_element_ids", {
            relationship.id: Neo4jGraphWidget.__get_neo4j_element_id(relationship)
            for relationship in getattr(graph, "relationships", ())
        })

    @staticmethod
    def __get_neo4j_item_text(element: Dict) -> Union[str, None]:
        lowercase_element_props = {key.lower(): value for key, value in element.get("properties", {}).items()}
        for key in NEO4J_LABEL_KEYS:
            if key in lowercase_element_props:
                return str(lowercase_element_props[key])
        return None

    # def __configuration_mapper_factory(binding_key: str, configurations: Dict[str, Dict[str, str]],
    #                                    default_mapping: Callable) -> Callable[[int, Dict], Union[Dict, str]]:

    @staticmethod
    def __configuration_mapper_factory(binding_key: str,
                                       configurations: Dict[str, Dict[str, str]]) -> Optional[
                                           Callable[[int, Dict], Optional[Union[Dict, str]]]]:
        """
        This is called once for each POSSIBLE_NODE_BINDINGS or POSSIBLE_EDGE_BINDINGS (as `binding_key` argument) and
        sets the returned mapping function for the `binding_key` on the core yFiles Graphs for Jupyter widget.

        Args:
            binding_key (str): One of POSSIBLE_NODE_BINDINGS or POSSIBLE_EDGE_BINDINGS
            configurations (Dict): All configured node or relationship configurations by the user, keyed by the node label or relationship type.
                For example, a dictionary built like:
                {
                  "Movie": { "color": "red", ... },
                  "Person": { "color": "blue", ... },
                  "*": { "color": "gray", ... }
                }
        Returns:
            Optional[Callable]: A mapping function for the yFiles Graphs for Jupyter core widget, or None to use
                its default mapping.
        """

        # GraphWidget resolves None to its built-in default mapping. Only install a
        # custom mapping when this binding is configured by the user.
        if not any(binding_key in configuration for configuration in configurations.values()):
            return None

        def mapping(index: int, item: Dict) -> Union[Dict, str, None]:
            label = item["properties"]["label"]  # yjg stores the neo4j node/relationship type in properties["label"]
            if ((label in configurations or "*" in configurations)
                    and binding_key in configurations.get(label, configurations.get("*"))):
                type_configuration = configurations.get(label, configurations.get("*"))
                if binding_key == "parent_configuration":
                    # the binding may be a lambda that must be resolved first
                    binding = type_configuration.get(binding_key)
                    if callable(binding):
                        binding = binding(item)
                    # parent_configuration binding may either resolve to a dict or a string
                    if isinstance(binding, dict):
                        group_label = binding.get("text", "")
                    else:
                        group_label = binding
                    result = "GroupNode" + group_label
                # mapping
                elif callable(type_configuration[binding_key]):
                    result = type_configuration[binding_key](item)
                # property name
                elif (not isinstance(type_configuration[binding_key], dict) and
                      type_configuration[binding_key] in item["properties"]):
                    result = item["properties"][type_configuration.get(binding_key)]
                # constant value
                else:
                    result = type_configuration.get(binding_key)

                return result

            if binding_key == "label":
                return Neo4jGraphWidget.__get_neo4j_item_text(item)
            else:
                # No custom value is configured for this item.
                return None

        return mapping

    def __apply_heat_mapping(self, configuration, widget: GraphWidget) -> None:
        setattr(widget, "heat_mapping",
                Neo4jGraphWidget.__configuration_mapper_factory("heat", configuration))

    def __create_group_nodes(self, configurations, widget: GraphWidget) -> None:
        group_node_properties = set()
        group_node_values = set()
        key = "parent_configuration"
        for node in widget.nodes:
            label = node["properties"]["label"]
            if label in configurations and key in configurations.get(label):
                group_node = configurations.get(label).get(key)

                if callable(group_node):
                    group_node = group_node(node)

                if isinstance(group_node, str):
                    # string or property value
                    if group_node in node["properties"]:
                        group_node_properties.add(str(node["properties"][group_node]))
                    else:
                        group_node_values.add(group_node)
                else:
                    # dictionary with values
                    text = group_node.get("text", "")
                    group_node_values.add(text)
                    configuration = {k: v for k, v in group_node.items() if k != "text"}
                    self.add_node_configuration(text, **configuration)

        for group_label in group_node_properties.union(group_node_values):
            node = {"id": "GroupNode" + group_label, "properties": {"label": group_label}}
            widget.nodes = [*widget.nodes, node]

    def __apply_parent_mapping(self, widget: GraphWidget) -> None:
        node_to_parent = {}
        edge_ids_to_remove = set()
        for edge in widget.edges[:]:
            rel_type = edge["properties"]["label"]
            for (parent_type, is_reversed) in self._parent_configurations:
                if rel_type == parent_type:
                    start = edge["start"]  # child node id
                    end = edge["end"]  # parent node id
                    if is_reversed:
                        node_to_parent[end] = start
                    else:
                        node_to_parent[start] = end
                    edge_ids_to_remove.add(edge["id"])
                    break

        # use list comprehension to filter out the edges to automatically trigger model sync with the frontend
        widget.edges = [edge for edge in widget.edges if edge["id"] not in edge_ids_to_remove]
        current_parent_mapping = getattr(widget, "node_parent_mapping", None)
        if current_parent_mapping is None:
            current_parent_mapping = lambda index, node: None
        setattr(widget, "node_parent_mapping",
                lambda index, node: node_to_parent.get(node["id"], current_parent_mapping(index, node)))

    def __apply_node_mappings(self, widget: GraphWidget) -> None:
        for key in POSSIBLE_NODE_BINDINGS:
            setattr(widget, f"node_{key}_mapping",
                    Neo4jGraphWidget.__configuration_mapper_factory(key, self._node_configurations))
        # manually set parent configuration
        setattr(widget, "node_parent_mapping",
                Neo4jGraphWidget.__configuration_mapper_factory("parent_configuration",
                                                                self._node_configurations))

    def __apply_edge_mappings(self, widget: GraphWidget) -> None:
        for key in POSSIBLE_EDGE_BINDINGS:
            setattr(widget, f"edge_{key}_mapping",
                    Neo4jGraphWidget.__configuration_mapper_factory(key, self._edge_configurations))

    def add_node_configuration(self, label: Union[str, list[str]], **kwargs: Dict[str, Any]) -> None:
        """
        Adds a configuration object for the given node `label`(s).

        Args:
            label (Union[str, list[str]]): The node label(s) for which this configuration should be used. Supports `*` to address all labels.
            **kwargs (Dict[str, Any]): Visualization configuration for the given node label. The following arguments are supported:

                - `text` (Union[str, Callable]): The text to be displayed on the node. By default, the node's label is used.
                - `color` (Union[str, Callable]): A convenience color binding for the node (see also styles kwarg).
                - `size` (Union[str, Callable]): The size of the node.
                - `styles` (Union[Dict, Callable]): A dictionary that may contain the following attributes color, shape (one of "ellipse", " hexagon", "hexagon2", "octagon", "pill", "rectangle", "round-rectangle" or "triangle"), image.
                - `property` (Union[Dict, Callable]): Allows to specify additional properties on the node, which may be bound by other bindings.
                - `type` (Union[Dict, Callable]): Defines a specific "type" for the node which affects the automatic positioning of nodes (same "type"s are preferred to be placed next to each other).
                - `parent_configuration` (Union[str, Callable]): Configure grouping for this node label.

        Returns:
            None
        """
        # this wrapper uses "text" as text binding in the graph
        # in contrast to "label" which is used in yfiles-jupyter-graphs
        text_binding = kwargs.pop("text", None)
        config = kwargs
        if text_binding is not None:
            config["label"] = text_binding

        cloned_config = {key: value for key, value in config.items()}
        if isinstance(label, list):
            for l in label:
                self._node_configurations[l] = cloned_config
        else:
            self._node_configurations[label] = cloned_config

    # noinspection PyShadowingBuiltins
    def add_relationship_configuration(self, type: Union[str, list[str]], **kwargs: Dict[str, Any]) -> None:
        """
        Adds a configuration object for the given relationship `type`(s).

        Args:
            type (Union[str, list[str]]): The relationship type(s) for which this configuration should be used. Supports `*` to address all labels.
            **kwargs (Dict): Visualization configuration for the given node label. The following arguments are supported:

                - `text` (Union[str, Callable]): The text to be displayed on the node.  By default, the relationship's type is used.
                - `color` (Union[str, Callable]): The relationship's color.
                - `thickness_factor` (Union[str, Callable]): The relationship's stroke thickness factor. By default, 1.
                - `property` (Union[Dict, Callable]): Allows to specify additional properties on the relationship, which may be bound by other bindings.

        Returns:
            None
        """
        # this wrapper uses "text" as text binding in the graph
        # in contrast to "label" which is used in yfiles-jupyter-graphs
        text_binding = kwargs.pop("text", None)
        config = kwargs
        if text_binding is not None:
            config["label"] = text_binding

        cloned_config = {key: value for key, value in config.items()}
        if isinstance(type, list):
            for t in type:
                self._edge_configurations[t] = cloned_config
        else:
            self._edge_configurations[type] = cloned_config

    # noinspection PyShadowingBuiltins
    def add_parent_relationship_configuration(self, type: Union[str, list[str]], reverse: Optional[bool] = False) -> None:
        """
        Configure specific relationship types to visualize as nested hierarchies. This removes these relationships from
        the graph and instead groups the related nodes (source and target) as parent-child.

        Args:
            type (Union[str, list[str]]): The relationship type(s) that should be visualized as node grouping hierarchy instead of the actual relationship.
            reverse (bool): Which node should be considered as parent. By default, the target node is considered as parent which can be reverted with this argument.

        Returns:
            None
        """
        if isinstance(type, list):
            for t in type:
                self._parent_configurations.add((t, reverse))
        else:
            self._parent_configurations.add((type, reverse))

    # noinspection PyShadowingBuiltins
    def del_node_configuration(self, label: Union[str, list[str]]) -> None:
        """
        Deletes the configuration object for the given node `label`(s).

        Args:
            label (Union[str, list[str]]): The node label(s) for which the configuration should be deleted. Supports `*` to address all labels.

        Returns:
            None
        """
        if isinstance(label, list):
            for l in label:
                Neo4jGraphWidget.__safe_delete_configuration(l, self._node_configurations)
        else:
            Neo4jGraphWidget.__safe_delete_configuration(label, self._node_configurations)

    # noinspection PyShadowingBuiltins
    def del_relationship_configuration(self, type: Union[str, list[str]]) -> None:
        """
        Deletes the configuration object for the given relationship `type`(s).

        Args:
            type (Union[str, list[str]]): The relationship type(s) for which the configuration should be deleted. Supports `*` to address all types.

        Returns:
            None
        """
        if isinstance(type, list):
            for t in type:
                Neo4jGraphWidget.__safe_delete_configuration(t, self._edge_configurations)
        else:
            Neo4jGraphWidget.__safe_delete_configuration(type, self._edge_configurations)

    @staticmethod
    def __safe_delete_configuration(key: str, configurations: Dict[str, Any]) -> None:
        if key == "*":
            configurations.clear()
        if key in configurations:
            del configurations[key]

    # noinspection PyShadowingBuiltins
    def del_parent_relationship_configuration(self, type: Union[str, list[str]]) -> None:
        """
        Deletes the relationship configuration for the given `type`(s).

        Args:
            type (Union[str, list[str]]): The relationship type(s) for which the configuration should be deleted.

        Returns:
            None
        """
        if isinstance(type, list):
            self._parent_configurations = {
                rel_type for rel_type in self._parent_configurations if rel_type[0] not in type
            }
        else:
            self._parent_configurations = {
                rel_type for rel_type in self._parent_configurations if rel_type[0] != type
            }

    def get_selected_node_ids(self, widget: Optional[Type["Neo4jGraphWidget"]] = None) -> List[Any | None]:
        """
        Returns the list of node ids that are currently selected in the most recently shown widget, or in the given `widget`.

        Args:
            widget (Optional[Type["Neo4jGraphWidget"]]): The widget from which the selected ids should be retrieved.
                If not specified, the most recently shown widget will be used.

        Returns:
            List[Any | None]: The list of selected Neo4j element IDs.
        """
        graph = self._widget
        if isinstance(widget, Neo4jGraphWidget):
            graph = widget._widget
        nodes, edges = graph.selection
        element_ids = getattr(graph, "_neo4j_node_element_ids", {})
        return [element_ids.get(node["id"], node["id"]) for node in nodes]

    def get_selected_relationship_ids(self, widget: Optional[Type["Neo4jGraphWidget"]] = None) -> List[Any | None]:
        """
        Returns the list of relationship ids that are currently selected in the most recently shown widget, or in the given `widget`.

        Args:
            widget (Optional[Type["Neo4jGraphWidget"]]): The widget from which the selected ids should be retrieved.
                If not specified, the most recently shown widget will be used.

        Returns:
            List[Any | None]: The list of selected Neo4j relationship element IDs.
        """
        graph = self._widget
        if isinstance(widget, Neo4jGraphWidget):
            graph = widget._widget
        nodes, edges = graph.selection
        element_ids = getattr(graph, "_neo4j_relationship_element_ids", {})
        return [element_ids.get(edge["id"], edge["id"]) for edge in edges]

    # region node_cell_mapping

    @property
    def node_cell_mapping(self) -> Union[str, Callable, None]:
        """
        Returns the currently specified node cell mapping.

        Returns:
            Union[str, Callable, None]: The currently specified node cell mapping.
        """
        return getattr(self, "_node_cell_mapping", None)

    @node_cell_mapping.setter
    def node_cell_mapping(self, node_cell_mapping: Optional[Union[str, Callable]]) -> None:
        """
        Specify a node to cell mapping to fine-tune automatic layout algorithms. The mapping should resolve to a row,
        column tuple that is used as a cell into which the node is placed.

        Args:
            node_cell_mapping (Optional[Union[str, Callable]]): Specifies a node to cell mapping. Must resolve to a row, column tuple or None.

        Returns:
            None
        """
        # noinspection PyAttributeOutsideInit
        self._node_cell_mapping = node_cell_mapping

    @node_cell_mapping.deleter
    def node_cell_mapping(self) -> None:
        """Deletes the node cell mapping."""
        self._node_cell_mapping = None

    def get_node_cell_mapping(self) -> Union[str, Callable, None]:
        """Legacy getter for the node cell mapping property.

        Deprecated, use ``widget.node_cell_mapping`` instead.
        """
        warnings.warn(
            "get_node_cell_mapping() is deprecated; use `widget.node_cell_mapping` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.node_cell_mapping

    def set_node_cell_mapping(self, node_cell_mapping: Optional[Union[str, Callable]]) -> None:
        """Legacy setter for the node cell mapping property.

        Deprecated, use ``widget.node_cell_mapping = value`` instead.
        """
        warnings.warn(
            "set_node_cell_mapping() is deprecated; use `widget.node_cell_mapping = value` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        self.node_cell_mapping = node_cell_mapping

    def del_node_cell_mapping(self) -> None:
        """Legacy deleter for the node cell mapping property.

        Deprecated, use ``widget.node_cell_mapping = None`` instead.
        """
        warnings.warn(
            "del_node_cell_mapping() is deprecated; use `widget.node_cell_mapping = None` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        self.node_cell_mapping = None

    # endregion
