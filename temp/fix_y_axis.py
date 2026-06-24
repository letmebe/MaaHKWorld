import json

# 修改test_scroll_menu.json
data = json.load(open('test_scroll_menu.json', encoding='utf-8'))
count = 0
for node_name, node in data.items():
    if node.get('custom_action') == 'MoveStickOnce':
        param_str = node.get('custom_action_param', '{}')
        param = json.loads(param_str)
        if param.get('stick') == 'right' and param.get('y', 0) > 0:
            old_y = param['y']
            param['y'] = -param['y']
            node['custom_action_param'] = json.dumps(param)
            count += 1
            print(f'{node_name}: y={old_y} -> y={param["y"]}')

with open('test_scroll_menu.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print(f'\ntest_scroll_menu.json: 共修改 {count} 个节点')

# 修改dispatch.json
data = json.load(open('dispatch.json', encoding='utf-8'))
count = 0
for node_name, node in data.items():
    if '滚动菜单' in node_name:
        param_str = node.get('custom_action_param', '{}')
        param = json.loads(param_str)
        if param.get('stick') == 'right' and param.get('y', 0) > 0:
            old_y = param['y']
            param['y'] = -param['y']
            node['custom_action_param'] = json.dumps(param)
            count += 1
            print(f'{node_name}: y={old_y} -> y={param["y"]}')

with open('dispatch.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print(f'\ndispatch.json: 共修改 {count} 个节点')