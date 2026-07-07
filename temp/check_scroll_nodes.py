import json
data = json.load(open('assets/resource/pipeline/dispatch.json', encoding='utf-8'))

# 查找所有滚动菜单节点
for node_name in sorted(data.keys()):
    if '滚动菜单' in node_name:
        node = data[node_name]
        print(f'{node_name}:')
        print(f'  recognition: {node.get("recognition", "无")}')
        print(f'  next: {node.get("next", [])}')
        print()