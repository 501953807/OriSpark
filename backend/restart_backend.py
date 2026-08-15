#!/usr/bin/env python3
"""重启 OriSpark 后端服务。"""
import os
import signal
import subprocess
import time

PORT = 8001
PROJECT_ROOT = "/Users/tangxiaochuan/AIWorkspace/ClaudeWorkspace/OriSpark/backend"

# 杀掉占用端口的进程
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
result = s.connect_ex(('127.0.0.1', PORT))
s.close()

if result == 0:
    # 端口被占用，查找并杀掉进程
    import subprocess
    result = subprocess.run(['lsof', '-ti:' + str(PORT)], capture_output=True, text=True)
    pids = result.stdout.strip().split('\n')
    for pid in pids:
        if pid:
            try:
                os.kill(int(pid), signal.SIGKILL)
                print(f"Killed PID {pid}")
            except:
                pass
    time.sleep(2)

# 启动新后端
env = os.environ.copy()
env['PYTHONPATH'] = PROJECT_ROOT
proc = subprocess.Popen(
    ['python3', '-m', 'uvicorn', 'app.main:app',
     '--host', '127.0.0.1', '--port', str(PORT), '--reload'],
    cwd=PROJECT_ROOT,
    env=env,
    stdout=open('/tmp/orispark.log', 'a'),
    stderr=subprocess.STDOUT,
)
print(f"Started backend with PID {proc.pid}")
print(f"Log: /tmp/orispark.log")
