import json
data = json.load(open('dispatch.json', encoding='utf-8'))

# 修改所有MoveToPosition节点，添加next_task参数
count = 0
for node_name, node in data.items():
    if node.get('custom_action') == 'MoveToPosition':
        param_str = node.get('custom_action_param', '{}')
        param = json.loads(param_str)
        
        # 从next推断next_task
        next_nodes = node.get('next', [])
        if next_nodes:
            # 假设下一个节点是移动准星循环节点
            next_task = next_nodes[0].replace('查找人员', '移动准星到人员')
            param['next_task'] = next_task
            node['custom_action_param'] = json.dumps(param)
            count += 1
            print(f'{node_name}: next_task={next_task}')

# 保存
with open('dispatch.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print(f'\n共修改 {count} 个节点')