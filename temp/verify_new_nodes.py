import json
data = json.load(open('assets/resource/pipeline/dispatch.json', encoding='utf-8'))

# 检查新增节点
new_nodes = [
    '探险派遣_打开菜单_秘禁之地',
    '探险派遣_移动准星到菜单顶部_秘禁之地',
    '探险派遣_打开菜单_稷下学院',
    '探险派遣_移动准星到菜单顶部_稷下学院'
]

print('新增节点：')
for node_name in new_nodes:
    if node_name in data:
        node = data[node_name]
        print(f'{node_name}:')
        print(f'  next: {node.get("next", [])}')
        print()