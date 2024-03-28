# yfiles_jupyter_graphs_for_neo4j
![A screenshot showing the yFiles graph widget for neo4j in a jupyter lab notebook](https://raw.githubusercontent.com/yWorks/yfiles-jupyter-graphs-for-neo4j/main/images/example.png)

Use yfiles_jupyter_graphs_for_neo4j to directly visualize [Neo4j](https://neo4j.com/) graphs with the yfiles_jupyter_graphs
widget. 

## Installation

TODO pypi upload. Once this package is uploaded to pypi, simply use 
```bash
    pip install yfiles_jupyter_graphs_for_neo4j
```
Or see README_DEV.md to build it yourself



## Documentation

Everything is in the one main class ```YfilesNeo4jGraphs```:

### YfilesNeo4jGraphs

- ```constructor```

    creates a new class instance with the following properties:

| Property           | Description                                                              | Default |
|--------------------|--------------------------------------------------------------------------|---------|
| ```driver```             | The given ```driver``` that is used to make cypher queries                     | ```None```    |
| ```widget_layout```      | Can be used to specify general widget appearance through css attributes  | ```None```    |
| ```overview_enabled```   | Enable graph overview component. Default behaviour depends on cell width | ```None```    |
| ```context_start_with``` | Specify context tab name to start with that tab opened                   | ```None```    |
| ```license```            | Specific activation license to use the widget                            | ```None```    |

### Methods 
- ```show_cypher(cypher, **kwargs)```
    - ```cypher```
      
        the [cypher query](https://neo4j.com/docs/cypher-manual/current/introduction/) used for the graph
    - ```**kwargs```
  
        any additional key word arguments (like parameters used in the cypher) are being directly passed onto the cypher

To show any graph, you need to have a driver. If you have not specified a driver when initiating the class, you can set a driver afterwards:

- ```set_driver(driver)```
    - ```driver```
        sets the given driver and uses this to send cypher queries to Databases
- ```get_driver()```
    Returns the current driver


The graph can be adjusted by adding configurations to each type with the following two functions:

- ```add_node_configuration(type, text='label', **kwargs)```
    - ```type```

        A configuration is added to this node type
    - ```text```
        
        The text will be the ```label``` in the generated graph. Hence, the default is the current ```label```, which is equal 
        to the type of Node
  
    - ```**kwargs``` 
        
        configurations are added here as keyword arguments. Possible keywords are ```size```, ```color```, ```style``` and ```type```
        
        The ```type``` keyword argument is referencing the yfiles_jupyter_graph type not the neo4j type.

  

- ```add_relationship_configuration(type, text='label', **kwargs)```
    - ```type```

        A configuration is added to this relationship type 
  
    - ```text```
        
        The text will be the ```label``` in the generated graph. Hence, the default is the current ```label```, which is equal 
        to the type of relationship
  
    - ```**kwargs``` 
        
        configurations are added here as keyword arguments. Possible keywords are ```color``` and ```thickness_factor```

To remove a configuration use the following two functions: 

- ```del_node_configuration(type)```
    
    deletes the configuration for ```type``` nodes
- ```del_relationship_configurations(type)```

    deletes the configuration for ```type``` relationships

You can select nodes and edges and get their ids. You can use the returned ids for new cyphers using these specific ids

- ```get_selected_node_ids(widget=None)```
    
    - ```widget``` 
    
        The widget that is used to select nodes from. If ```None``` is specified, the last one shown is used.
    
    Returns an Array of node ids

- ```get_selected_edge_ids(widget=None)```
    
    - ```widget``` 
    
        The widget that is used to select edges from. If ```None``` is specified, the last one shown is used.
    
    Returns an Array of edge ids
        