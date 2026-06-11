import urllib.request
import json

data = json.dumps({'query': 'Які кроки для вирішення CrashLoopBackOff?'}).encode()
req = urllib.request.Request('http://127.0.0.1:8080/query', data=data, headers={'Content-Type': 'application/json'})
resp = urllib.request.urlopen(req)
result = json.loads(resp.read())

print('=== POST /query RAG TEST ===')
print('Success:', result['success'])
print('Response:', result['response'])
