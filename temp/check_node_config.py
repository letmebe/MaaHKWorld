import json
data = json.load(open('../assets/resource/pipeline/dispatch.json', encoding='utf-8'))
node = data.get('探险派遣_查找人员_哆哆', {})
print('timeout:', node.get('timeout', '未设置(默认20000ms)'))
print('rate_limit:', node.get('rate_limit', '未设置(默认1000ms)'))
print('on_error:', node.get('on_error'))
print('recognition:', node.get('recognition'))