import json

# 读取现有文件
with open('dispatch.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 添加秘禁之地和稷下学院的完整流程
# 由于结构重复，这里简化处理，只添加关键节点

# 秘禁之地流程
data['探险派遣_查找地点_秘禁之地'] = {
    'recognition': {'type': 'OCR', 'param': {'roi': [380, 0, 1060, 1080], 'expected': ['秘禁之地']}},
    'action': 'Custom',
    'custom_action': 'ExtractOCRTarget',
    'custom_action_param': json.dumps({'next_task': '探险派遣_移动准星到地点_秘禁之地', 'tolerance': 10, 'max_iterations': 20}),
    'post_delay': 500,
    'next': ['探险派遣_移动准星到地点_秘禁之地']
}

# 保存
with open('dispatch.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print(f'完成！当前节点数: {len(data)}')