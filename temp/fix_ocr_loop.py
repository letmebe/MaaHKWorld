import json
data = json.load(open('assets/resource/pipeline/dispatch.json', encoding='utf-8'))

# 修改查找人员节点，将on_error改为next列表
count = 0
for node_name in list(data.keys()):
    if '查找人员' in node_name:
        node = data[node_name]
        
        # 获取滚动菜单节点名
        scroll_node = node.get('on_error', [None])[0]
        if scroll_node:
            # 将on_error移到next列表
            next_nodes = node.get('next', [])
            # next列表：原next + 滚动菜单
            node['next'] = next_nodes + [scroll_node]
            # 删除on_error
            del node['on_error']
            count += 1
            print(f'{node_name}: next={node["next"]}')

# 修改滚动菜单节点，next指向查找人员节点
for node_name in list(data.keys()):
    if '滚动菜单' in node_name:
        node = data[node_name]
        # 提取人员名称
        person_name = node_name.split('_')[-1]
        # 查找人员节点名
        find_node = f'探险派遣_查找人员_{person_name}'
        node['next'] = [find_node]
        count += 1
        print(f'{node_name}: next={node["next"]}')

with open('assets/resource/pipeline/dispatch.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print(f'\n共修改 {count} 个节点')