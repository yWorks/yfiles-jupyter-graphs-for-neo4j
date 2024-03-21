"""Jupyter (ipy)widget powered by yFiles.

The main YfilesNeo4jGraphs class is defined in this module.

"""
from yfiles_jupyter_graphs import GraphWidget
from typing import Optional, Any

#TODO maybe change to get dynamically when adding bindings

POSSIBLE_NODE_BINDINGS = {'color', 'size', 'label'}
POSSIBLE_EDGE_BINDINGS = {'color', 'thickness_factor', 'label'}
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

        for key in POSSIBLE_NODE_BINDINGS:
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

        for key in POSSIBLE_EDGE_BINDINGS:
            def wrapper(key):
                def mapping(index, edge):
                    label = edge["properties"]["label"]
                    if label in self._edge_configurations and key in self._edge_configurations.get(label):
                        # mapping
                        if callable(self._edge_configurations.get(label)[key]):
                            return self._edge_configurations.get(label)[key](edge)
                        # property name
                        elif self._edge_configurations.get(label)[key] in edge["properties"]:
                            return edge["properties"][self._edge_configurations.get(label).get(key)]
                        #value
                        else:
                            return self._edge_configurations.get(label).get(key)
                    default = getattr(widget, f"default_edge_{key}_mapping")
                    return default(index, edge)

                return mapping

            setattr(widget, f"_edge_{key}_mapping", wrapper(key))

    def add_node_configuration(self, type, textbinding='label', color=None, size=None):
        config = {'label': textbinding, 'color': color, 'size': size}
        self._node_configurations[type] = {key: value for key, value in config.items() if value is not None}


    def add_relation_configuration(self, type, textbinding='label', color=None, thickness=None):
        config = {'label': textbinding, 'color': color, 'thickness_factor': thickness}
        self._edge_configurations[type] = {key: value for key, value in config.items() if value is not None}


    def del_node_configuration(self, type):
        if type in self._node_configurations:
            del self._node_configurations[type]

    def del_edge_configuration(self, type):
        if type in self._edge_configurations:
            del self._edge_configurations[type]
