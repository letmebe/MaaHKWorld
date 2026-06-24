import json

data = json.load(open('assets/resource/pipeline/dispatch.json', encoding='utf-8'))

# 人员列表（按选择顺序）
persons = ['阿噗', '啾啾', '哆哆', '卫宁', '堂听虎', '小红', '学典鹅', '酷酷', '聪聪']

count = 0

print("修改计划：\n")

for person in persons:
    # 1. 修改滚动菜单节点：next改为空数组
    scroll_node_name = f'探险派遣_滚动菜单_{person}'
    if scroll_node_name in data:
        old_next = data[scroll_node_name].get('next', [])
        data[scroll_node_name]['next'] = []
        print(f'{scroll_node_name}:')
        print(f'  原 next: {old_next}')
        print(f'  新 next: []')
        count += 1
    
    # 2. 修改选择人员节点
    select_node_name = f'探险派遣_选择人员_{person}'
    if select_node_name in data:
        current_next = data[select_node_name].get('next', [])
        if current_next:
            first_next = current_next[0]
            
            # 判断是否是查找人员节点（以"查找人员"开头）
            if '查找人员' in first_next:
                # 提取下一个人员名称
                next_person = first_next.split('_')[-1]
                # 修改为：[查找人员节点, '[JumpBack]滚动菜单节点]
                new_next = [first_next, f'[JumpBack]探险派遣_滚动菜单_{next_person}']
                data[select_node_name]['next'] = new_next
                print(f'{select_node_name}:')
                print(f'  原 next: {current_next}')
                print(f'  新 next: {new_next}')
                count += 1
            else:
                # 是确认派遣节点，不修改
                print(f'{select_node_name}: 保持不变（确认派遣节点）')
    
    print()

with open('assets/resource/pipeline/dispatch.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print(f'共修改 {count} 个节点')
