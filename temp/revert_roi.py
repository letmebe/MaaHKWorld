import json

# 读取文件
with open('dispatch.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 改回去：1920 -> 630
count = 0
for node_name, node in data.items():
    if 'recognition' in node and isinstance(node['recognition'], dict):
        if 'param' in node['recognition'] and 'roi' in node['recognition']['param']:
            roi = node['recognition']['param']['roi']
            if len(roi) == 4 and roi[2] == 1920:
                roi[2] = 630
                count += 1
                print(f'{node_name}: ROI宽度 1920 -> 630')

# 保存
with open('dispatch.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print(f'\n已改回：共修改 {count} 个节点')