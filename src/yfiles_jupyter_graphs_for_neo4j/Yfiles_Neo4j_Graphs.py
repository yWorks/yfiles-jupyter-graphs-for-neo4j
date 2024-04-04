"""Jupyter (ipy)widget powered by yFiles.

The main YfilesNeo4jGraphs class is defined in this module.

"""
from yfiles_jupyter_graphs import GraphWidget

# TODO maybe change to get dynamically when adding bindings

POSSIBLE_NODE_BINDINGS = {'color', 'size', 'type', 'styles', 'scale_factor', 'position', 'layout', 'property', 'label'}
POSSIBLE_EDGE_BINDINGS = {'color', 'thickness_factor', 'property', 'label'}


class YfilesNeo4jGraphs:
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

    def show_cypher(self, cypher, **kwargs):
        """
        main function
        :param cypher: str, Send a data query to the neo4j database
               **kwargs: variable declarations usable in cypher
        """
        if self._driver is not None:
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
