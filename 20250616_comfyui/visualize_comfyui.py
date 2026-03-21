import json
from graphviz import Digraph

def visualize_comfyui(json_path: str, out_path: str = "graph"):
    with open(json_path, 'r') as f:
        data = json.load(f)

    dot = Digraph(format="png")
    id_to_name = {}

    # ノード名とIDをマッピング
    for node in data["nodes"]:
        nid = str(node["id"])
        name = node.get("type", f"Node_{nid}")
        id_to_name[nid] = name
        dot.node(nid, f"{name}\n(id={nid})")

    # リンクからエッジを作成
    for link in data["links"]:
        from_id, to_id = str(link[1]), str(link[3])
        dot.edge(from_id, to_id)

    dot.render(out_path, view=True)
    print(f"✅ グラフを出力しました: {out_path}.png")

# 使用例
filename = "your_workflow_2"
visualize_comfyui(f"{filename}.json", out_path=filename)
