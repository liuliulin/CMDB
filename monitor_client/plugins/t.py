import datetime

now = datetime.datetime.now()
tmp = now.strftime("%Y-%m-%d")
print(tmp)
file = open(r'D:\PDSSshare\redme.txt', 'w')
file.write(tmp)
file.close()
