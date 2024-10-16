"""Jupyter (ipy)widget powered by yFiles.

The main Neo4jGraphWidget class is defined in this module.

"""
from typing import Dict
import inspect

from yfiles_jupyter_graphs import GraphWidget

# TODO maybe change to get dynamically when adding bindings

POSSIBLE_NODE_BINDINGS = {'coordinate', 'color', 'size', 'type', 'styles', 'scale_factor', 'position',
                          'layout', 'property', 'label'}
POSSIBLE_EDGE_BINDINGS = {'color', 'thickness_factor', 'property', 'label'}
NEO4J_LABEL_KEYS = ['name', 'title', 'text', 'description', 'caption', 'label']

class Neo4jGraphWidget:
    def __init__(self, driver=None, widget_layout=None,
                 overview_enabled=None, context_start_with=None, license=None,
                 autocomplete_relationships=False, graph_layout='organic'):
        self._widget = GraphWidget()
        self._driver = driver
        self._session = driver.session()
        self._license = license
        self._overview = overview_enabled
        self._layout = widget_layout
        self._context_start_with = context_start_with
        self.set_autocomplete_relationships(autocomplete_relationships)
        self._graph_layout = graph_layout

        self._node_configurations = {}
        self._edge_configurations = {}
        self._parent_configurations = set()

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
            raise ValueError("autocomplete_relationships must be a bool, a string, or a list of strings")
        if isinstance(autocomplete_relationships, str):
            self._autocomplete_relationships = [autocomplete_relationships]
        else:
            self._autocomplete_relationships = autocomplete_relationships

    def _is_autocomplete_enabled(self):
        if isinstance(self._autocomplete_relationships, bool):
            return self._autocomplete_relationships
        return len(self._autocomplete_relationships) > 0

    def _get_relationship_types_expression(self):
        if isinstance(self._autocomplete_relationships, list) and len(self._autocomplete_relationships) > 0:
            return "AND type(rel) IN $relationship_types"
        return ""

    def show_cypher(self, cypher, graph_layout=None, **kwargs):
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
            self.__create_group_nodes(self._node_configurations, widget)
            self.__apply_node_mappings(widget)
            self.__apply_edge_mappings(widget)
            self.__apply_heat_mapping({**self._node_configurations, **self._edge_configurations}, widget)
            self.__apply_parent_mapping(widget)
            if graph_layout is None:
                widget.set_graph_layout(**dict(algorithm=self._graph_layout))
            else:
                widget.set_graph_layout(**dict(algorithm=graph_layout))

            self._widget = widget
            widget.show()
        else:
            raise Exception("no driver specified")

    @staticmethod
    def __get_neo4j_item_text(element: Dict):
        lowercase_element_props = {key.lower(): value for key, value in element.get('properties', {}).items()}
        for key in NEO4J_LABEL_KEYS:
            if key in lowercase_element_props:
                return str(lowercase_element_props[key])
        return None

    @staticmethod
    def __configuration_mapper_factory(binding_key, configurations, default_mapping):
        def mapping(index, item: Dict):
            label = item["properties"]["label"]  # yjg stores the neo4j node/relationship type in properties["label"]
            if label in configurations and binding_key in configurations.get(label):
                # mapping
                if callable(configurations.get(label)[binding_key]):
                    result = configurations.get(label)[binding_key](item)
                # property name
                elif (not isinstance(configurations.get(label)[binding_key], dict) and
                      configurations.get(label)[binding_key] in item["properties"]):
                    result = item["properties"][configurations.get(label).get(binding_key)]
                # constant value or dictionary
                elif binding_key == 'parent_configuration':
                    if isinstance(configurations.get(label).get(binding_key), dict):
                        result = configurations.get(label).get(binding_key).get('text', '')
                    else:
                        result = configurations.get(label).get(binding_key)
                # constant value
                else:
                    result = configurations.get(label).get(binding_key)
                if binding_key != 'parent_configuration':
                    return result
                else:
                    return 'GroupNode' + str(result)

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

    def __apply_heat_mapping(self, configuration, widget):
        setattr(widget, "_heat_mapping",
                Neo4jGraphWidget.__configuration_mapper_factory('heat', configuration,
                                                                getattr(widget, 'default_heat_mapping')))

    def __create_group_nodes(self, configurations, widget):
        group_node_properties = set()
        group_node_values = set()
        key = 'parent_configuration'
        for node in widget.nodes:
            label = node['properties']['label']
            if label in configurations and key in configurations.get(label):
                group_node = configurations.get(label).get(key)
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

    def __apply_parent_mapping(self, widget):

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

    def __apply_node_mappings(self, widget):
        for key in POSSIBLE_NODE_BINDINGS:
            default_mapping = getattr(widget, f"default_node_{key}_mapping")
            setattr(widget, f"_node_{key}_mapping",
                    Neo4jGraphWidget.__configuration_mapper_factory(key, self._node_configurations, default_mapping))
        # manually set parent configuration
        setattr(widget, f"_node_parent_mapping",
                Neo4jGraphWidget.__configuration_mapper_factory('parent_configuration',
                                                                self._node_configurations, lambda node: None))

    def __apply_edge_mappings(self, widget):
        for key in POSSIBLE_EDGE_BINDINGS:
            default_mapping = getattr(widget, f"default_edge_{key}_mapping")
            setattr(widget, f"_edge_{key}_mapping",
                    Neo4jGraphWidget.__configuration_mapper_factory(key, self._edge_configurations, default_mapping))

    def add_node_configuration(self, label, **kwargs):
        # this wrapper uses "text" as text binding in the graph
        # in contrast to "label" which is used in yfiles-jupyter-graphs
        text_binding = kwargs.pop("text", None)
        config = kwargs
        if text_binding is not None:
            config["label"] = text_binding
        self._node_configurations[label] = {key: value for key, value in config.items()}

    def add_relationship_configuration(self, type, **kwargs):
        # this wrapper uses "text" as text binding in the graph
        # in contrast to "label" which is used in yfiles-jupyter-graphs
        text_binding = kwargs.pop("text", None)
        config = kwargs
        if text_binding is not None:
            config["label"] = text_binding
        self._edge_configurations[type] = {key: value for key, value in config.items()}

    def add_parent_relationship_configuration(self, type, reverse=False):
        self._parent_configurations.add((type, reverse))

    def del_node_configuration(self, type):
        if type in self._node_configurations:
            del self._node_configurations[type]

    def del_relationship_configuration(self, type):
        if type in self._edge_configurations:
            del self._edge_configurations[type]

    def del_parent_relationship_configuration(self, type):
        self._parent_configurations = {
            rel_type for rel_type in self._parent_configurations if rel_type[0] != type
        }

    def get_selected_node_ids(self, widget=None):
        graph = widget if widget is not None else self._widget
        nodes, edges = graph.get_selection()
        return list(map(lambda node: node['id'], nodes))

    def get_selected_relationship_ids(self, widget=None):
        graph = widget if widget is not None else self._widget
        nodes, edges = graph.get_selection()
        return list(map(lambda edge: edge['id'], edges))
