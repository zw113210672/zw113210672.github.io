# 推送到 GitHub - 由 push_to_github.bat 调用
# 这个脚本处理中文路径，避免 cmd 编码问题

import subprocess, sys, os
from datetime import date

BASE = "D:\\选股软件\\hermes选股\\website"
os.chdir(BASE)

print("=" * 40)
print("Push trading records to GitHub")
print("=" * 40)
print()

# 1. 生成今日记录
print("[1/3] Generate today report...")
r = subprocess.run([sys.executable, "generate_site.py"], capture_output=True, text=True)
print(r.stdout.strip())
if r.stderr.strip():
    print("STDERR:", r.stderr.strip())
if r.returncode != 0:
    input("Generate failed! Press Enter to exit...")
    sys.exit(1)

# 2. Git add & commit
print()
print("[2/3] Git commit...")
subprocess.run(["git", "add", "-A"], check=True)
today = date.today().strftime("%Y-%m-%d")
r = subprocess.run(["git", "commit", "-m", f"Daily update {today}"], capture_output=True, text=True)
print(r.stdout.strip())
if r.stderr.strip():
    print(r.stderr.strip())

# 3. Git push
print()
print("[3/3] Push to GitHub...")
r = subprocess.run(["git", "push"], capture_output=True, text=True)
print(r.stdout.strip())
if r.stderr.strip():
    print(r.stderr.strip())

print()
print("Done! https://zw113210672.github.io")
print()
input("Press Enter to exit...")
