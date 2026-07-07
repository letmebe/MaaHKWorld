import json
data = json.load(open('dispatch.json', encoding='utf-8'))
node = data.get('探险派遣_查找人员_哆哆', {})
print('节点名: 探险派遣_查找人员_哆哆')
print('recognition:', node.get('recognition'))
print('action:', node.get('action'))
print('next:', node.get('next'))
print('on_error:', node.get('on_error'))
print('timeout:', node.get('timeout', '未设置(默认20000ms)'))