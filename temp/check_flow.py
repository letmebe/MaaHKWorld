import json

data = json.load(open('assets/resource/pipeline/dispatch.json', encoding='utf-8'))

# 人员列表（按选择顺序）
persons = ['阿噗', '啾啾', '哆哆', '卫宁', '堂听虎', '小红', '学典鹅', '酷酷', '聪聪']

print("当前流程：\n")
for i, person in enumerate(persons):
    select_node_name = f'探险派遣_选择人员_{person}'
    if select_node_name in data:
        next_nodes = data[select_node_name].get('next', [])
        print(f'{i+1}. 选择{person} → {next_nodes}')

print("\n\n需要修改的逻辑：")
print("选择人员节点 → next = [查找下一个人员, JumpBack滚动菜单]")