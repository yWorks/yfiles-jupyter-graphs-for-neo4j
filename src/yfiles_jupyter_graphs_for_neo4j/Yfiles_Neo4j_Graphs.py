"""Jupyter (ipy)widget powered by yFiles.

The main YfilesNeo4jGraphs class is defined in this module.

"""
from yfiles_jupyter_graphs import GraphWidget
from typing import Optional, Any

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
            widget.set_node_styles_mapping(lambda node: self._node_configurations.get(node["properties"]["label"], {}))
            widget.set_node_label_mapping(lambda node: node["properties"][
                self._node_configurations.get(node["properties"]["label"], {"label": "label"})["label"]])

            widget.show()
        else:
            raise Exception("no driver specified")


    #TODO add more bindings
    def add_node_configuration(self, type, textbinding=None, color=None):
        if textbinding is not None and color is not None:
            self._node_configurations[type] = {'label': textbinding, 'color': color}
        elif textbinding is None and color is not None:
            self._node_configurations[type] = {'color': color}
        elif textbinding is not None and color is None:
            self._node_configurations[type] = {'label': textbinding}


    def add_relation_configuration(self, type, textbinding=None, color=None):
        if textbinding is not None and color is not None:
            self._edge_configurations[type] = {'label': textbinding, 'color': color}
        elif textbinding is None and color is not None:
            self._edge_configurations[type] = {'color': color}
        elif textbinding is not None and color is None:
            self._edge_configurations[type] = {'label': textbinding}
