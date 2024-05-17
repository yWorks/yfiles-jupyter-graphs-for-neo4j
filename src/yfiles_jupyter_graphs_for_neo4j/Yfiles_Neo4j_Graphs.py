"""Jupyter (ipy)widget powered by yFiles.

The main Neo4jGraphWidget class is defined in this module.

"""
from yfiles_jupyter_graphs import GraphWidget

# TODO maybe change to get dynamically when adding bindings

POSSIBLE_NODE_BINDINGS = {'color', 'size', 'type', 'styles', 'scale_factor', 'position', 'layout', 'property', 'label'}
POSSIBLE_EDGE_BINDINGS = {'color', 'thickness_factor', 'property', 'label'}


class Neo4jGraphWidget:
    _driver = None
    _node_configurations = {}
    _edge_configurations = {}
    _widget = GraphWidget()

    def __init__(self, driver=None, widget_layout=None,
                 overview_enabled=None, context_start_with='About', license=None):
        if driver is not None:
            self._driver = driver
        self._session = driver.session()
        self._license = license
        self._overview = overview_enabled
        self._layout = widget_layout
        self._context_start_with = context_start_with
        self._autocomplete_relationships = False

    def set_driver(self, driver):
        """
        Setter for the driver attribute.
        If a new driver is used, there is also a new session
        :param driver: neo4j._sync.driver.Neo4jDriver

        """
        self._driver = driver
        self._session = driver.session()

    def get_driver(self):
        """
        Getter for the driver attribute
        :return: neo4j._sync.driver.Neo4jDriver
        """
        return self._driver

    def set_autocomplete_relationships(self, autocomplete_relationships):
        """
        Sets the flag to enable or disable autocomplete for relationships.
        When autocomplete is enabled, relationships are automatically completed in the graph,
        similar to the behavior in Neo4j Browser.
        This can be set to True/False to enable or disable for all relationships,
        or a single relationship type or a list of relationship types to enable for specific relationships.
        :param autocomplete_relationships: bool | str | list[str]
        """
        if not isinstance(autocomplete_relationships, (bool, str, list)):
            raise ValueError("autocomplete_relationships must be a bool or a list of strings")
        if isinstance(autocomplete_relationships, str):
            self._autocomplete_relationships = [autocomplete_relationships]
        else:
            self._autocomplete_relationships = autocomplete_relationships

    def _is_autocomplete_enabled(self):
        if isinstance(self._autocomplete_relationships, bool):
            return self._autocomplete_relationships
        return len(self._autocomplete_relationships) > 0

    def _get_relationship_types_expression(self):
        if self._autocomplete_relationships == True:
            return ""
        elif len(self._autocomplete_relationships) > 0:
            return "AND type(rel) IN $relationship_types"
        return ""

    def show_cypher(self, cypher, **kwargs):
        """
        main function
        :param cypher: str, Send a data query to the neo4j database
               **kwargs: variable declarations usable in cypher
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
            self.apply_node_mappings(widget)
            self.apply_edge_mappings(widget)

            self._widget = widget
            widget.show()
        else:
            raise Exception("no driver specified")

    def apply_node_mappings(self, widget):

        for key in POSSIBLE_NODE_BINDINGS:
            def wrapper(current_key):
                def mapping(index, node):
                    label = node["properties"]["label"]
                    if label in self._node_configurations and current_key in self._node_configurations.get(label):
                        # mapping
                        if callable(self._node_configurations.get(label)[current_key]):
                            return self._node_configurations.get(label)[current_key](node)
                        # property name
                        elif self._node_configurations.get(label)[current_key] in node["properties"]:
                            return node["properties"][self._node_configurations.get(label).get(current_key)]
                        # constant value
                        else:
                            return self._node_configurations.get(label).get(current_key)
                    default = getattr(widget, f"default_node_{current_key}_mapping")
                    return default(index, node)

                return mapping

            setattr(widget, f"_node_{key}_mapping", wrapper(key))

    def apply_edge_mappings(self, widget):

        for key in POSSIBLE_EDGE_BINDINGS:
            def wrapper(current_key):
                def mapping(index, edge):
                    label = edge["properties"]["label"]
                    if label in self._edge_configurations and current_key in self._edge_configurations.get(label):
                        # mapping
                        if callable(self._edge_configurations.get(label)[current_key]):
                            return self._edge_configurations.get(label)[current_key](edge)
                        # property name
                        elif self._edge_configurations.get(label)[current_key] in edge["properties"]:
                            return edge["properties"][self._edge_configurations.get(label).get(current_key)]
                        # constant value
                        else:
                            return self._edge_configurations.get(label).get(current_key)
                    default = getattr(widget, f"default_edge_{current_key}_mapping")
                    return default(index, edge)

                return mapping

            setattr(widget, f"_edge_{key}_mapping", wrapper(key))

    def add_node_configuration(self, label, **kwargs):
        # this wrapper uses "text" as text binding in the graph
        # in contrast to "label" which is used in yfiles-jupyter-graphs
        text_binding = kwargs.pop("text", 'label')
        config = kwargs
        if text_binding is not None:
            config["label"] = text_binding
        self._node_configurations[label] = {key: value for key, value in config.items()}

    def add_relationship_configuration(self, type, **kwargs):
        # this wrapper uses "text" as text binding in the graph
        # in contrast to "label" which is used in yfiles-jupyter-graphs
        text_binding = kwargs.pop("text", 'label')
        config = kwargs
        if text_binding is not None:
            config["label"] = text_binding
        self._edge_configurations[type] = {key: value for key, value in config.items()}

    def del_node_configuration(self, type):
        if type in self._node_configurations:
            del self._node_configurations[type]

    def del_relationship_configuration(self, type):
        if type in self._edge_configurations:
            del self._edge_configurations[type]

    def get_selected_node_ids(self, widget=None):
        graph = widget if widget is not None else self._widget
        nodes, edges = graph.get_selection()
        return list(map(lambda node: node['id'], nodes))

    def get_selected_relationship_ids(self, widget=None):
        graph = widget if widget is not None else self._widget
        nodes, edges = graph.get_selection()
        return list(map(lambda edge: edge['id'], edges))
