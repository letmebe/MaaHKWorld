import json
data = json.load(open('dispatch.json', encoding='utf-8'))

# 修改所有滚动菜单节点，将x=30000,y=10000改为x=10000,y=30000
count = 0
for node_name, node in data.items():
    if '滚动菜单' in node_name:
        param_str = node.get('custom_action_param', '{}')
        param = json.loads(param_str)
        if param.get('x') == 30000 and param.get('y') == 10000:
            param['x'] = 10000
            param['y'] = 30000
            node['custom_action_param'] = json.dumps(param)
            count += 1
            print(f'{node_name}: x=10000, y=30000')

# 保存
with open('dispatch.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print(f'\n共修改 {count} 个节点')