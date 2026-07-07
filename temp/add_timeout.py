import json
data = json.load(open('dispatch.json', encoding='utf-8'))

# 为所有查找人员节点增加超时时间
count = 0
for node_name in data:
    if '查找人员' in node_name:
        data[node_name]['timeout'] = 60000  # 60秒
        count += 1
        print(f'{node_name}: timeout=60000')

# 保存
with open('dispatch.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print(f'\n共修改 {count} 个节点')