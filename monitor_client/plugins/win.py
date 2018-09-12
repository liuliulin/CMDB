import subprocess

s = subprocess.Popen("python", stdout=subprocess.PIPE, stdin=subprocess.PIPE, shell=True)
s.stdin.write(b"import os\n")
s.stdin.write(b"print(os.getcwd())")
s.stdin.close()

out = s.stdout.read().decode("Big5")
s.stdout.close()
print(out)
