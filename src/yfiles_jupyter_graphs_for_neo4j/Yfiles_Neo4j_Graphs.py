"""Jupyter (ipy)widget powered by yFiles.

The main YfilesNeo4jGraphs class is defined in this module.

"""
from yfiles_jupyter_graphs import GraphWidget
from typing import Optional, Any

class YfilesNeo4jGraphs:
    _driver = None

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

    def show_cypher(self, cypher):
        """
        main function
        :param cypher: str, Send a data query to the neo4j database
        """
        if self._driver is not None:
            widget = GraphWidget(graph=self._session.run(cypher).graph())
            widget.show()
        else:
            raise Exception("no driver specified")

