# 校验 stop12 网页 JSON 注入正确性
import json, re
h = open('dividend_dashboard_stop12.html', encoding='utf8').read()
ok = True
for name in ['STARTS','SHORTS','CODES','COLORS','STATS','SERIES','ROWS']:
    m = re.search(r'const '+name+r' = (.*?);', h, re.S)
    if m:
        try:
            v = json.loads(m.group(1))
            print(name, 'OK', type(v).__name__)
        except Exception as e:
            ok = False
            print(name, 'PARSE_ERR', e)
    else:
        ok = False
        print(name, 'MISSING')
print('SERIES has rec_days_loss:', ('rec_days_loss' in (re.search(r'const SERIES = (.*?);', h, re.S).group(1) if re.search(r'const SERIES = (.*?);', h, re.S) else '')))
print('ALL_OK' if ok else 'HAS_ERROR')