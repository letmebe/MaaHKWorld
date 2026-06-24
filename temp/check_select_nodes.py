import json
data = json.load(open('assets/resource/pipeline/dispatch.json', encoding='utf-8'))

# 查找所有选择人员节点
for node_name in sorted(data.keys()):
    if '选择人员' in node_name:
        node = data[node_name]
        print(f'{node_name}:')
        print(f'  next: {node.get("next", [])}')
        print(f'  timeout: {node.get("timeout", "无")}')
        print()