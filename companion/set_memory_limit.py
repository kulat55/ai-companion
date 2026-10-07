# 放开核心记忆块（persona / human）的字符上限。
# 用法：python set_memory_limit.py [每块上限，默认 100000]
# 说明：长期记忆（全部对话 / 事件 / 归档）存在数据库，本就无上限；
#       此脚本放开的是“每轮必带的核心记忆块”，默认从 5000 提到 100000。
import sys
import json
import urllib.request

BASE = 'http://127.0.0.1:8283'
CORE_LABELS = ('persona', 'human')


def req(method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(BASE + path, data=data, method=method,
                               headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(r) as f:
        return json.loads(f.read().decode())


def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 100000
    agents = req('GET', '/v1/agents')
    for a in agents:
        d = req('GET', '/v1/agents/' + a['id'])
        for b in d['memory']['blocks']:
            if b['label'] in CORE_LABELS:
                req('PATCH', '/v1/blocks/' + b['id'], {'limit': limit})
                print('%-18s %-7s -> %s (当前 %s 字)' %
                      (a['name'], b['label'], limit, len(b['value'])))
    print('done：核心记忆块上限已设为', limit)


if __name__ == '__main__':
    main()
