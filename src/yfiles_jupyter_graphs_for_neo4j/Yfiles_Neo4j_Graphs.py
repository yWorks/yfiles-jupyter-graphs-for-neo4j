"""Jupyter (ipy)widget powered by yFiles.

The main Neo4jGraphWidget class is defined in this module.

"""
from typing import Any, Callable, Dict, Union, Type, Optional, List
from types import FunctionType, MethodType
import inspect

from yfiles_jupyter_graphs import GraphWidget

# TODO maybe change to get dynamically when adding bindings

POSSIBLE_NODE_BINDINGS = {'coordinate', 'color', 'size', 'type', 'styles', 'scale_factor', 'position',
                          'layout', 'property', 'label'}
POSSIBLE_EDGE_BINDINGS = {'color', 'thickness_factor', 'property', 'label'}
NEO4J_LABEL_KEYS = ['name', 'title', 'text', 'description', 'caption', 'label']

class Neo4jGraphWidget:
    """
    A yFiles Graphs for Jupyter widget that is tailored to visualize Cypher queries resolved against a Neo4j database.
    """

    # noinspection PyShadowingBuiltins
    def __init__(self, driver: Optional[Any] = None, widget_layout: Optional[Any] = None,
                 overview_enabled: Optional[bool] = None, context_start_with: Optional[str] = None,
                 license: Optional[Dict] = None,
                 autocomplete_relationships: Optional[bool] = False, layout: Optional[str] = 'organic'):
        """
        Initializes a new instance of the Neo4jGraphWidget class.

        Args:
            driver (Optional[neo4j._sync.driver.Neo4jDriver]): The Neo4j driver to resolve the Cypher queries.
            widget_layout (Optional[ipywidgets.Layout]): Can be used to specify general widget appearance through css attributes.
                See ipywidgets documentation for the available keywords.
            overview_enabled (Optional[bool]): Whether the graph overview is enabled or not.
            context_start_with (Optional[str]): Start with a specific side-panel opened in the interactive widget.
            license (Optional[Dict]): The widget works on common public domains without a specific license.
                For unknown domains, a license can be obtained by the creators of the widget.
            autocomplete_relationships (Optional[bool]): Whether missing relationships in the Cypher's return value are automatically added.
            layout (Optional[str]): Specifies the default automatic graph arrangement. Can be overwritten for each
                cypher separately. By default, an "organic" layout is used. Supported values are:
                    - "circular"
                    - "hierarchic"
                    - "organic"
                    - "interactive_organic_layout"
                    - "orthogonal"
                    - "radial"
                    - "tree"
                    - "map"
                    - "orthogonal_edge_router"
                    - "organic_edge_router"
        """

        self._widget = GraphWidget()
        self._driver = driver
        self._session = driver.session()
        self._license = license
        self._overview = overview_enabled
        self._layout = widget_layout
        self._context_start_with = context_start_with
        self.set_autocomplete_relationships(autocomplete_relationships)
        self._graph_layout = layout

        self._node_configurations = {}
        self._edge_configurations = {}
        self._parent_configurations = set()

    def set_driver(self, driver: Any) -> None:
        """
        The Neo4j driver that is used to resolve the Cypher queries. A new session is created when set.

        Args:
            driver (neo4j._sync.driver.Neo4jDriver): The Neo4j driver to resolve the Cypher queries.

        Returns:
            None
        """
        self._driver = driver
        self._session = driver.session()

    def get_driver(self):
        """
        Gets the configured Neo4j driver.

        Returns:
            neo4j._sync.driver.Neo4jDriver
        """
        return self._driver

    def set_autocomplete_relationships(self, autocomplete_relationships: Union[bool, str, list[str]]) -> None:
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

    def _is_autocomplete_enabled(self) -> bool:
        if isinstance(self._autocomplete_relationships, bool):
            return self._autocomplete_relationships
        return len(self._autocomplete_relationships) > 0

    def _get_relationship_types_expression(self) -> str:
        if isinstance(self._autocomplete_relationships, list) and len(self._autocomplete_relationships) > 0:
            return "AND type(rel) IN $relationship_types"
        return ""

    def show_cypher(self, cypher: str, layout: Optional[str] = None, **kwargs: Dict[str, Any]) -> None:
        """
        Displays the given Cypher query as interactive graph.

        Args:
            cypher (str): The Cypher query whose result should be visualized as graph.
            layout (Optional[str]): The graph layout for this request. Overwrites the general default `layout` that was
                specified when initializing the class. Supported values are:
                    - "circular"
                    - "hierarchic"
                    - "organic"
                    - "interactive_organic_layout"
                    - "orthogonal"
                    - "radial"
                    - "tree"
                    - "map"
                    - "orthogonal_edge_router"
                    - "organic_edge_router"
            **kwargs (Dict[str, Any]): Additional parameters that should be passed to the Cypher query.

        Returns:
            None

        Raises:
            Exception: If no driver was specified.
        """
        if self._driver is not None:
            if self._is_autocomplete_enabled():
                nodes = self._session.run(cypher, **kwargs).graph().nodes
                node_ids = [node.element_id for node in nodes]
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
            widget = GraphWidget(overview_enabled=self._overview, context_start_with=self._context_start_with,
                                 widget_layout=self._layout, license=self._license,
                                 graph=self._session.run(cypher, **kwargs).graph())
            self.__create_group_nodes(self._node_configurations, widget)
            self.__apply_node_mappings(widget)
            self.__apply_edge_mappings(widget)
            self.__apply_heat_mapping({**self._node_configurations, **self._edge_configurations}, widget)
            self.__apply_parent_mapping(widget)
            if layout is None:
                widget.set_graph_layout(self._graph_layout)
            else:
                widget.set_graph_layout(layout)

            widget.node_cell_mapping = self.node_cell_mapping

            self._widget = widget
            widget.show()
        else:
            raise Exception("no driver specified")

    @staticmethod
    def __get_neo4j_item_text(element: Dict) -> Union[str, None]:
        lowercase_element_props = {key.lower(): value for key, value in element.get('properties', {}).items()}
        for key in NEO4J_LABEL_KEYS:
            if key in lowercase_element_props:
                return str(lowercase_element_props[key])
        return None

    @staticmethod
    def __configuration_mapper_factory(binding_key: str, configurations: Dict[str, Dict[str, str]],
                                       default_mapping: Callable) -> Callable[[int, Dict], Union[Dict, str]]:
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
            default_mapping (MethodType): A reference to the default binding of the yFiles Graphs for Jupyter core widget that should be used when the binding_key is not specified otherwise.

        Returns:
            FunctionType: A mapping function that can used in the yFiles Graphs for Jupyter core widget.
        """

        def mapping(index: int, item: Dict) -> Union[Dict, str]:
            label = item["properties"]["label"]  # yjg stores the neo4j node/relationship type in properties["label"]
            if ((label in configurations or '*' in configurations)
                    and binding_key in configurations.get(label, configurations.get('*'))):
                type_configuration = configurations.get(label, configurations.get('*'))
                if binding_key == 'parent_configuration':
                    # the binding may be a lambda that must be resolved first
                    binding = type_configuration.get(binding_key)
                    if callable(binding):
                        binding = binding(item)
                    # parent_configuration binding may either resolve to a dict or a string
                    if isinstance(binding, dict):
                        group_label = binding.get('text', '')
                    else:
                        group_label = binding
                    result = 'GroupNode' + group_label
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
                # call default mapping
                # some default mappings do not support "index" as first parameter
                parameters = inspect.signature(default_mapping).parameters
                if len(parameters) > 1 and parameters[list(parameters)[0]].annotation == int:
                    return default_mapping(index, item)
                else:
                    return default_mapping(item)

        return mapping

    def __apply_heat_mapping(self, configuration, widget: GraphWidget) -> None:
        setattr(widget, "_heat_mapping",
                Neo4jGraphWidget.__configuration_mapper_factory('heat', configuration,
                                                                getattr(widget, 'default_heat_mapping')))

    def __create_group_nodes(self, configurations, widget: GraphWidget) -> None:
        group_node_properties = set()
        group_node_values = set()
        key = 'parent_configuration'
        for node in widget.nodes:
            label = node['properties']['label']
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
                    text = group_node.get('text', '')
                    group_node_values.add(text)
                    configuration = {k: v for k, v in group_node.items() if k != 'text'}
                    self.add_node_configuration(text, **configuration)

        for group_label in group_node_properties.union(group_node_values):
            node = {'id': 'GroupNode' + group_label, 'properties': {'label': group_label}}
            widget.nodes = [*widget.nodes, node]

    def __apply_parent_mapping(self, widget: GraphWidget) -> None:
        node_to_parent = {}
        edge_ids_to_remove = set()
        for edge in widget.edges[:]:
            rel_type = edge["properties"]["label"]
            for (parent_type, is_reversed) in self._parent_configurations:
                if rel_type == parent_type:
                    start = edge['start']  # child node id
                    end = edge['end']  # parent node id
                    if is_reversed:
                        node_to_parent[end] = start
                    else:
                        node_to_parent[start] = end
                    edge_ids_to_remove.add(edge['id'])
                    break

        # use list comprehension to filter out the edges to automatically trigger model sync with the frontend
        widget.edges = [edge for edge in widget.edges if edge['id'] not in edge_ids_to_remove]
        current_parent_mapping = getattr(widget, '_node_parent_mapping')
        setattr(widget, "_node_parent_mapping",
                lambda index, node: node_to_parent.get(node['id'], current_parent_mapping(index, node)))

    def __apply_node_mappings(self, widget: GraphWidget) -> None:
        for key in POSSIBLE_NODE_BINDINGS:
            default_mapping = getattr(widget, f"default_node_{key}_mapping")
            setattr(widget, f"_node_{key}_mapping",
                    Neo4jGraphWidget.__configuration_mapper_factory(key, self._node_configurations, default_mapping))
        # manually set parent configuration
        setattr(widget, f"_node_parent_mapping",
                Neo4jGraphWidget.__configuration_mapper_factory('parent_configuration',
                                                                self._node_configurations, lambda node: None))

    def __apply_edge_mappings(self, widget: GraphWidget) -> None:
        for key in POSSIBLE_EDGE_BINDINGS:
            default_mapping = getattr(widget, f"default_edge_{key}_mapping")
            setattr(widget, f"_edge_{key}_mapping",
                    Neo4jGraphWidget.__configuration_mapper_factory(key, self._edge_configurations, default_mapping))

    def add_node_configuration(self, label: str, **kwargs: Dict[str, Any]) -> None:
        """
        Adds a configuration object for the given node `label`.

        Args:
            label (str): The node label for which this configuration should be used.
            **kwargs (Dict): Visualization configuration for the given node label. The following arguments are supported:

                - `text` (Union[str, Callable]): The text to be displayed on the node. By default, the node's label is used.
                - `color` (Union[str, Callable]): A convenience color binding for the node (see also styles kwarg).
                - `size` (Union[str, Callable]): The size of the node.
                - `styles` (Union[Dict, Callable]): A dictionary that may contain the following attributes color, shape (one of 'ellipse', ' hexagon', 'hexagon2', 'octagon', 'pill', 'rectangle', 'round-rectangle' or 'triangle'), image.
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
        self._node_configurations[label] = {key: value for key, value in config.items()}

    # noinspection PyShadowingBuiltins
    def add_relationship_configuration(self, type: str, **kwargs: Dict[str, Any]) -> None:
        """
        Adds a configuration object for the given node `label`.

        Args:
            type (str): The relationship type for which this configuration should be used.
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
        self._edge_configurations[type] = {key: value for key, value in config.items()}

    # noinspection PyShadowingBuiltins
    def add_parent_relationship_configuration(self, type: str, reverse=False) -> None:
        """
        Configure specific relationship types to visualize as nested hierarchies. This removes these relationships from
        the graph and instead groups the related nodes (source and target) as parent-child.

        Args:
            type (str): The relationship type that should be visualized as node grouping hierarchy instead of the actual relationship.
            reverse (bool): Which node should be considered as parent. By default, the target node is considered as parent which can be reverted with this argument.

        Returns:
            None
        """
        self._parent_configurations.add((type, reverse))

    # noinspection PyShadowingBuiltins
    def del_node_configuration(self, type: str) -> None:
        """
        Deletes the configuration object for the given node `label`.

        Args:
            type (str): The node label for which the configuration should be deleted.

        Returns:
            None
        """
        if type in self._node_configurations:
            del self._node_configurations[type]

    # noinspection PyShadowingBuiltins
    def del_relationship_configuration(self, type: str) -> None:
        """
        Deletes the configuration object for the given relationship `type`.

        Args:
            type (str): The relationship type for which the configuration should be deleted.

        Returns:
            None
        """
        if type in self._edge_configurations:
            del self._edge_configurations[type]

    # noinspection PyShadowingBuiltins
    def del_parent_relationship_configuration(self, type: str) -> None:
        """
        Deletes the relationship configuration for the given `type`.

        Args:
            type (str): The relationship type for which the configuration should be deleted.

        Returns:
            None
        """
        self._parent_configurations = {
            rel_type for rel_type in self._parent_configurations if rel_type[0] != type
        }

    def get_selected_node_ids(self, widget: Optional[Type["Neo4jGraphWidget"]]=None) -> List[str]:
        """
        Returns the list of node ids that are currently selected in the most recently shown widget, or in the given `widget`.

        Args:
            widget (Optional[Type["Neo4jGraphWidget"]]): The widget from which the selected ids should be retrieved.
                If not specified, the most recently shown widget will be used.

        Returns:
            List[str]: The list of node ids currently selected in the widget.
        """
        graph = widget if widget is not None else self._widget
        nodes, edges = graph.get_selection()
        return list(map(lambda node: node['id'], nodes))

    def get_selected_relationship_ids(self, widget: Optional[Type["Neo4jGraphWidget"]]=None) -> List[str]:
        """
        Returns the list of relationship ids that are currently selected in the most recently shown widget, or in the given `widget`.

        Args:
            widget (Optional[Type["Neo4jGraphWidget"]]): The widget from which the selected ids should be retrieved.
                If not specified, the most recently shown widget will be used.

        Returns:
            List[str]: The list of relationship ids currently selected in the widget.
        """
        graph = widget if widget is not None else self._widget
        nodes, edges = graph.get_selection()
        return list(map(lambda edge: edge['id'], edges))

    def get_node_cell_mapping(self) -> Union[str, Callable, None]:
        """
        Returns the currently specified node cell mapping.

        Returns:
            Union[str, Callable, None]: The currently specified node cell mapping.
        """
        return self._node_cell_mapping if hasattr(self, '_node_cell_mapping') else None

    def set_node_cell_mapping(self, node_cell_mapping: Union[str, Callable]) -> None:
        """
        Specify a node to cell mapping to fine-tune automatic layout algorithms. The mapping should resolve to a row,
        column tuple that is used as a cell into which the node is placed.

        Args:
            node_cell_mapping (Union[str, Callable]): Specifies a node to cell mapping. Must resolve to a row, column tuple or None.

        Returns:
            None
        """
        # noinspection PyAttributeOutsideInit
        self._node_cell_mapping = node_cell_mapping

    def del_node_cell_mapping(self) -> None:
        """
        Deletes the node cell mapping.

        Returns:
             None
        """
        if hasattr(self, '_node_cell_mapping'):
            delattr(self, '_node_cell_mapping')

    node_cell_mapping = property(get_node_cell_mapping, set_node_cell_mapping, del_node_cell_mapping)