# yFiles Jupyter Graphs for Neo4j Agent Guide

Reference for coding agents working with `yfiles-jupyter-graphs-for-neo4j`.
This package is a small Neo4j-specific wrapper around
[`yfiles-jupyter-graphs`](https://github.com/yWorks/yfiles-jupyter-graphs). It
executes Cypher with the Neo4j Python driver and renders the resulting graph in
a Jupyter notebook.

## Install

```bash
pip install yfiles_jupyter_graphs_for_neo4j neo4j
```

The package requires Python 3.8 or newer and depends on
`yfiles_jupyter_graphs~=2.0`.

For Google Colab, enable the custom widget manager before rendering:

```python
try:
    from google.colab import output
    output.enable_custom_widget_manager()
except ImportError:
    pass
```

## Core import pattern

```python
from neo4j import GraphDatabase
from yfiles_jupyter_graphs_for_neo4j import Neo4jGraphWidget
```

`Neo4jGraphWidget` is exported from the package root. It is a wrapper, not a
subclass of the core `GraphWidget`; use its public methods and properties
described below.

## Minimal working example

```python
from neo4j import GraphDatabase
from yfiles_jupyter_graphs_for_neo4j import Neo4jGraphWidget

driver = GraphDatabase.driver(
    "neo4j://localhost:7687",
    auth=("neo4j", "password"),
    database="neo4j",
)

graph = Neo4jGraphWidget(driver)
graph.show_cypher(
    "MATCH (source)-[relationship]->(target) "
    "RETURN source, relationship, target LIMIT 20"
)
```

`show_cypher` renders the widget and returns `None`; it is normally the last
expression in a notebook cell. Do not call `display(graph)` expecting the
wrapper itself to render.

Do not commit database credentials. Prefer environment variables or a secret
manager in real notebooks and examples.

## Connecting and querying

### Constructor

```python
Neo4jGraphWidget(
    driver=None,
    widget_layout=None,
    overview_enabled=None,
    context_start_with=None,
    license=None,
    autocomplete_relationships=False,
    layout="organic",
)
```

| Argument | Description |
| --- | --- |
| `driver` | A Neo4j Python driver. A session is created when the driver is assigned. Pass a valid driver before querying. |
| `widget_layout` | An `ipywidgets.Layout` or compatible layout value forwarded to the core widget. |
| `overview_enabled` | Whether the graph overview is enabled. `None` lets the core widget choose its default. |
| `context_start_with` | The side panel to open initially, if any. |
| `license` | An optional yFiles license dictionary for domains that require one. |
| `autocomplete_relationships` | `False`, `True`, one relationship type, or a list of relationship types. |
| `layout` | Default graph layout. The default is `"organic"`. |

Although `driver` has a `None` type default for API compatibility, the current
implementation creates a session in the driver setter. A usable Neo4j driver is
therefore required for construction and for `show_cypher`.

Assigning a new driver is supported and creates a new session:

```python
graph.driver = another_driver
```

### `show_cypher`

```python
graph.show_cypher(cypher, layout=None, **parameters)
```

- `cypher` is the query whose Neo4j graph result should be visualized.
- `layout` overrides the constructor default for this render only.
- Additional keyword arguments are passed to `driver.session().run`, so use
  Neo4j parameter names as keyword arguments.

Queries should return Neo4j nodes and relationships, for example:

```python
graph.show_cypher(
    "MATCH (movie:Movie {released: $year})<-[:ACTED_IN]-(person) "
    "RETURN person, movie LIMIT 20",
    year=1999,
)
```

With the default `autocomplete_relationships=False`, only the nodes and
relationships represented by the query's graph result are shown. The query is
executed through the Neo4j driver's `.graph()` result conversion.

## Relationship autocompletion

Autocompletion is useful when a query returns nodes but omits the relationships
between them, similar to Neo4j Browser:

```python
graph.autocomplete_relationships = True       # all relationship types
graph.show_cypher("MATCH (person:Person) RETURN person LIMIT 10")
```

It can also be restricted to relationship types:

```python
graph.autocomplete_relationships = "ACTED_IN"
# or: graph.autocomplete_relationships = ["ACTED_IN", "DIRECTED"]
```

When enabled, the wrapper first runs the supplied query to collect node IDs,
then runs a second query that returns those nodes and relationships connecting
them. The second query uses undirected matching, so relationships in either
direction can be included. Re-render after changing this property.

## Layouts

The layout is forwarded to the core yFiles widget. Use these string values:

| Value | Typical use |
| --- | --- |
| `"organic"` | General-purpose force-directed layout; default |
| `"interactive_organic"` | Force-directed layout suitable for interaction |
| `"hierarchical"` | Layered or flow-like graphs |
| `"circular"` | Ring layout with bundled edges |
| `"circular_straight_line"` | Ring layout with straight edges |
| `"orthogonal"` | Structured, grid-like diagrams |
| `"radial"` | A central node with concentric levels |
| `"tree"` | Tree-shaped data |
| `"map"` | Geographic coordinates from `coordinate` mapping |
| `"orthogonal_edge_router"` | Reroute edges while preserving node positions |
| `"organic_edge_router"` | Smooth organic edge routing |

For example:

```python
graph.show_cypher(
    "MATCH (source)-[relationship]->(target) "
    "RETURN source, relationship, target LIMIT 30",
    layout="hierarchical",
)
```

The source documentation also mentions `"hierarchic"` in the constructor
argument list, but `"hierarchical"` is the canonical value used by the core
widget and the example notebooks.

## Configuration bindings

Configurations are stored on the wrapper and applied when `show_cypher` creates
the underlying widget. If a configuration is changed after a graph was shown,
call `show_cypher` again to see the change.

### Binding resolution

Node and relationship configuration values may be:

- a callable receiving the normalized graph item dictionary;
- a string naming a key in `item["properties"]`; or
- a constant value.

For a string, the wrapper first looks for an exact property-key match. If the
key is absent, the string is used as a constant. A callable should therefore
usually be written like `lambda item: ...`, not as a function expecting a raw
Neo4j `Node` or `Relationship` object.

Example:

```python
graph.add_node_configuration(
    "Person",
    text="name",                         # property binding
    color=lambda node: "#4A90D9" if node["properties"].get("active") else "#AAAAAA",
    size=(60, 60),                        # constant binding
    styles={"shape": "ellipse"},
)
graph.add_relationship_configuration(
    "ACTED_IN",
    text="role",
    color="#AC94F4",
    thickness_factor=2,
)
```

The wrapper uses `text` as the public name for the label binding. Internally it
maps `text` to the core widget's `label` binding.

### Node configuration

```python
graph.add_node_configuration(label, **configuration)
```

`label` can be a string, a list of labels, or `"*"` for a wildcard. Supported
configuration keys include:

- `text`: displayed text; property key, constant, or callable;
- `color`: convenience color binding;
- `size`: `(width, height)` or a binding;
- `styles`: a yFiles node-style dictionary or binding, such as
  `{"shape": "rectangle", "color": "#2196F3"}`;
- `coordinate`: `(latitude, longitude)`-style coordinates for map layouts;
- `position`: a position binding;
- `layout`: a complete layout/bounds binding;
- `scale_factor`: a node scale-factor binding;
- `property`: additional property data or a binding;
- `type`: a layout type hint;
- `heat`: a normalized heat value or binding;
- `parent_configuration`: an artificial or property-derived group parent.

If no `text` configuration is supplied, the default text lookup checks
properties case-insensitively in this order:

```text
name, title, text, description, caption, label
```

### Relationship configuration

```python
graph.add_relationship_configuration(type, **configuration)
```

`type` can be a string, a list of relationship types, or `"*"`. Supported keys
include `text`, `color`, `thickness_factor`, `styles`, `property`, and `heat`.
The relationship type is used as the default label when no more suitable label
property is available.

Wildcard configurations provide defaults, but an explicit label/type
configuration replaces the wildcard configuration for that item:

```python
graph.add_relationship_configuration("*", color="#999999")
graph.add_relationship_configuration("DIRECTED", color="#D32F2F")
```

The override is at configuration level, not per individual field. Include all
fields that an explicit configuration needs.

### Heat mapping

Heat values must be normalized to the range `[0.0, 1.0]` before being returned:

```python
def heat(item):
    amount = item["properties"].get("amount")
    if amount is None:
        return 0
    return max(0, min(1, amount / 100_000_000))

graph.add_node_configuration("Filing", heat=heat)
```

### Geographic coordinates

Use `coordinate` bindings together with the `"map"` layout. The callable must
return the coordinate tuple expected by the core widget or `None`:

```python
graph.add_node_configuration(
    "City",
    coordinate=lambda node: (
        node["properties"]["latitude"],
        node["properties"]["longitude"],
    ),
)
graph.show_cypher(
    "MATCH (city:City) RETURN city",
    layout="map",
)
```

### Node-to-cell mapping

`node_cell_mapping` gives automatic layouts a preferred `(row, column)` cell:

```python
graph.node_cell_mapping = lambda node: (
    0 if node["properties"].get("important") else 1,
    0,
)
```

It may also be a property-key string or `None`. Delete it with
`del graph.node_cell_mapping` or clear it with `graph.node_cell_mapping = None`.

## Grouping and nesting

### Relationship-based hierarchy

`add_parent_relationship_configuration` removes matching relationships from the
rendered edge list and represents them as parent-child nesting:

```python
graph.add_parent_relationship_configuration("COUNTRY")
graph.show_cypher(
    "MATCH (entity:Entity)-[r:COUNTRY]->(country:Country) "
    "RETURN entity, r, country"
)
```

By default, the relationship target is the parent and the source is the child.
Use `reverse=True` when the source should be the parent. The method accepts a
single relationship type or a list:

```python
graph.add_parent_relationship_configuration(["COUNTRY", "CONCERNS"], reverse=True)
```

Each node can have one parent. Chained parent relationships can produce
multi-level nesting.

### Artificial group nodes

Set `parent_configuration` in a node configuration to create groups that do
not exist in Neo4j:

```python
graph.add_node_configuration("Entity", parent_configuration="Entities")
graph.add_node_configuration(
    "Country",
    parent_configuration={"text": "Countries", "color": "#2196F3"},
)
```

For a string value, the wrapper treats the string as a property key when that
key exists on the node; otherwise it uses the string literally as the group
label. A callable can return either a string or a dictionary with a `text` key
and optional style/configuration keys.

## Removing configurations

```python
graph.del_node_configuration("Entity")
graph.del_node_configuration(["Person", "Movie"])
graph.del_relationship_configuration("DIRECTED")
graph.del_parent_relationship_configuration("COUNTRY")
```

Passing `"*"` to a node or relationship deletion clears all configurations of
that kind. As with additions, render the query again after deleting a
configuration.

## Reading selections

The selection helpers return stable Neo4j element IDs, not the internal IDs
used by the yFiles graph widget:

```python
selected_ids = graph.get_selected_node_ids()
selected_relationship_ids = graph.get_selected_relationship_ids()

graph.show_cypher(
    "MATCH (source)-[relationship]->(target) "
    "WHERE elementId(source) IN $ids "
    "RETURN source, relationship, target",
    ids=selected_ids,
)
```

The helpers read the most recently rendered widget when no argument is given.
To read another wrapper's selection, pass that `Neo4jGraphWidget` instance:

```python
ids = graph_a.get_selected_node_ids(graph_b)
```

Selections are held by the frontend widget. Re-running a cell that recreates
the graph, restarting the kernel, or replacing the rendered widget can reset
the selection; read the IDs before doing so.

## Deprecated compatibility methods

Prefer direct property access. These methods remain for backwards
compatibility and emit `DeprecationWarning`:

```python
graph.set_driver(driver)
graph.get_driver()
graph.set_autocomplete_relationships(True)
graph.get_node_cell_mapping()
graph.set_node_cell_mapping(mapping)
graph.del_node_cell_mapping()
```

Use `graph.driver`, `graph.autocomplete_relationships`, and
`graph.node_cell_mapping` instead.

## Important implementation notes

- The wrapper creates a fresh core `GraphWidget` for every `show_cypher` call.
  The private `graph._widget` object is an implementation detail and should not
  be used as a stable public API.
- Configuration callables receive normalized dictionaries whose graph data is
  in `item["properties"]`. Do not assume every item has every property,
  especially artificial group nodes.
- Automatic layouts may overwrite position mappings. Use the core widget's
  no-layout option only when preserving supplied positions is required; this
  wrapper's public default is automatic layout.
- `add_parent_relationship_configuration` changes the displayed structure by
  removing those relationship edges. Do not expect configured parent
  relationships to remain selectable as edges.
- The canonical relationship deletion method is
  `del_relationship_configuration` (singular).

## Further reading

- [README](https://raw.githubusercontent.com/yWorks/yfiles-jupyter-graphs-for-neo4j/refs/heads/main/README.md)
- [Basic example](https://raw.githubusercontent.com/yWorks/yfiles-jupyter-graphs-for-neo4j/refs/heads/main/examples/basic_example.ipynb)
- [Configuration example](https://github.com/yWorks/yfiles-jupyter-graphs-for-neo4j/blob/main/examples/configurations_example.ipynb)
- [Selection example](https://github.com/yWorks/yfiles-jupyter-graphs-for-neo4j/blob/main/examples/selection_example.ipynb)
- [Grouping example](https://github.com/yWorks/yfiles-jupyter-graphs-for-neo4j/blob/main/examples/grouping.ipynb)
- [Feature example](https://github.com/yWorks/yfiles-jupyter-graphs-for-neo4j/blob/main/examples/feature_example.ipynb)
- [yFiles Graphs for Jupyter documentation](https://yworks.github.io/yfiles-jupyter-graphs/)
- [Neo4j Cypher manual](https://neo4j.com/docs/cypher-manual/current/introduction/)
