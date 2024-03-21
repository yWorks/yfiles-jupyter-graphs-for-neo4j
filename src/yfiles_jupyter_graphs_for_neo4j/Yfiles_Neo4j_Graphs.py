"""Jupyter (ipy)widget powered by yFiles.

The main YfilesNeo4jGraphs class is defined in this module.

"""
from yfiles_jupyter_graphs import GraphWidget
from typing import Optional, Any

POSSIBLE_BINDINGS = {'color', 'label'}

class YfilesNeo4jGraphs:
    _driver = None
    _node_configurations = {}
    _edge_configurations = {}

    def __init__(self, driver: Optional[Any] = None):
        if driver is not None:
            self._driver = driver
            self._session = driver.session()


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
            widget = GraphWidget(graph=self._session.run(cypher, **kwargs).graph())
            self.apply_node_mappings(widget)
            self.apply_edge_mappings(widget)

            widget.show()
        else:
            raise Exception("no driver specified")

    def apply_node_mappings(self, widget):

        for key in POSSIBLE_BINDINGS:
            def wrapper(key):
                def mapping(index, node):
                    label = node["properties"]["label"]
                    if label in self._node_configurations and key in self._node_configurations.get(label):
                        if self._node_configurations.get(label)[key] in node["properties"]:
                            return node["properties"][self._node_configurations.get(label).get(key)]
                        else:
                            return self._node_configurations.get(label).get(key)
                    default = getattr(widget, f"default_node_{key}_mapping")
                    return default(index, node)
                return mapping

            setattr(widget, f"_node_{key}_mapping", wrapper(key))


    def apply_edge_mappings(self, widget):

        for key in POSSIBLE_BINDINGS:
            def wrapper(key):
                def mapping(index, edge):
                    label = edge["properties"]["label"]
                    if label in self._edge_configurations and key in self._edge_configurations.get(label):
                        if self._edge_configurations.get(label)[key] in edge["properties"]:
                            return edge["properties"][self._edge_configurations.get(label).get(key)]
                        else:
                            return self._edge_configurations.get(label).get(key)
                    default = getattr(widget, f"default_edge_{key}_mapping")
                    return default(index, edge)

                return mapping

            setattr(widget, f"_edge_{key}_mapping", wrapper(key))

    def add_node_configuration(self, type, textbinding='label', color=None):
        config = {'label': textbinding, 'color': color}
        self._node_configurations[type] = {key: value for key, value in config.items() if value is not None}


    def add_relation_configuration(self, type, textbinding='label', color=None):
        config = {'label': textbinding, 'color': color}
        self._edge_configurations[type] = {key: value for key, value in config.items() if value is not None}
