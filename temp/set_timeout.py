import json
data = json.load(open('../assets/resource/pipeline/dispatch.json', encoding='utf-8'))

# 为所有选择人员节点设置timeout
count = 0
for node_name in data:
    if '选择人员' in node_name:
        data[node_name]['timeout'] = 60000
        count += 1
        print(f'{node_name}: timeout=60000')

with open('../assets/resource/pipeline/dispatch.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print(f'\n共修改 {count} 个节点')