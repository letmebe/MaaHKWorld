import json
data = json.load(open('dispatch.json', encoding='utf-8'))

# 将MoveToPosition替换为MoveStick
count = 0
for node_name, node in data.items():
    if node.get('custom_action') == 'MoveToPosition':
        # 获取参数
        param_str = node.get('custom_action_param', '{}')
        param = json.loads(param_str)
        target_x = param.get('target_x', 960)
        target_y = param.get('target_y', 540)
        
        # 替换为MoveStick
        node['custom_action'] = 'MoveStick'
        node['custom_action_param'] = json.dumps({
            'target_x': target_x,
            'target_y': target_y,
            'tolerance': 10,
            'max_iterations': 20,
            'stick': 'left'
        })
        count += 1
        print(f'{node_name}: MoveToPosition -> MoveStick')

# 保存
with open('dispatch.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print(f'\n共修改 {count} 个节点')