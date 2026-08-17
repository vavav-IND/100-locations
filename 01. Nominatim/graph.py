import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt

# --- Rebuild the graph from your saved Excel (no OSRM calls needed) ---
df = pd.read_excel("NetworkX_Routes.xlsx")

G = nx.DiGraph()

for i, row in df.iterrows():
    src = row["Source"]
    dst = row["Destination"]
    G.add_edge(src, dst, weight=row["Road_Distance"])

# --- Draw the graph ---
plt.figure(figsize=(20, 15))  # large canvas so labels don't overlap

# spring_layout automatically positions nodes nicely
pos = nx.spring_layout(G, seed=42, k=2)

# Draw nodes
nx.draw_networkx_nodes(G, pos, node_size=500, node_color="skyblue")

# Draw edges
nx.draw_networkx_edges(G, pos, arrows=True, arrowsize=15,
                       edge_color="gray", width=1)

# Draw node labels (city names)
nx.draw_networkx_labels(G, pos, font_size=7, font_weight="bold")

# Draw edge weight labels (distances)
edge_labels = nx.get_edge_attributes(G, "weight")
edge_labels = {k: f"{v} km" for k, v in edge_labels.items()}
nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=5)

plt.title("Road Network Graph", fontsize=16)
plt.axis("off")  # hide the x/y axis
plt.tight_layout()
plt.savefig("graph.png", dpi=150, bbox_inches="tight")  # save as image
plt.show()  # also display it

print("Graph saved as graph.png")