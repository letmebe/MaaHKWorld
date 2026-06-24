import json
data = json.load(open('../assets/resource/pipeline/dispatch.json', encoding='utf-8'))

# 将选择人员节点的timeout从60000改为3000
count = 0
for node_name in data:
    if '选择人员' in node_name and data[node_name].get('timeout') == 60000:
        data[node_name]['timeout'] = 3000
        count += 1
        print(f'{node_name}: timeout=3000ms')

with open('../assets/resource/pipeline/dispatch.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print(f'\n共修改 {count} 个节点')