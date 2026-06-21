import json
data = json.load(open('../assets/resource/pipeline/dispatch.json', encoding='utf-8'))
node = data.get('探险派遣_选择人员_啾啾', {})
print('探险派遣_选择人员_啾啾:')
print('  timeout:', node.get('timeout', '未设置(默认20000ms)'))
print('  next:', node.get('next'))