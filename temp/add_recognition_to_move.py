import json
data = json.load(open('dispatch.json', encoding='utf-8'))

# 修改MoveToPosition节点，添加recognition和on_error
count = 0
for node_name, node in data.items():
    if node.get('custom_action') == 'MoveToPosition':
        # 添加准星识别
        node['recognition'] = 'Custom'
        node['custom_recognition'] = 'FindCrosshair'
        node['custom_recognition_param'] = json.dumps({'threshold': 0.8})
        # 添加on_error循环
        node['on_error'] = [node_name]
        count += 1
        print(f'{node_name}: 添加recognition和on_error')

# 保存
with open('dispatch.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print(f'\n共修改 {count} 个节点')