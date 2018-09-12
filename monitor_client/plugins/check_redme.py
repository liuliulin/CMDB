import datetime

mail_list = ['F3234383@foxera.com', 'F3234475@foxera.com', 'F7400343@foxera.com',
             'Cesar@foxera.com', ]


def SendeMail():
    import smtplib
    from email.mime.text import MIMEText
    from email.utils import formataddr
    msg = MIMEText("(10.134.99.163)文件服务器同步异常，请重新同步！", 'plain', 'utf-8')
    msg['From'] = formataddr(["F7400343", 'F7400343@foxera.com'])
    msg['To'] = formataddr(["F7400343", 'F7400343@foxera.com'])
    msg['Subject'] = "同步异常"

    server = smtplib.SMTP("10.150.7.41", 25)
    server.login("F7400343@foxera.com", "Foxconn99")
    server.sendmail("F7400343@foxera.com", mail_list, msg.as_string())
    server.quit()


if __name__ == "__main__":
    now = datetime.datetime.now()
    tmp = now.strftime("%Y-%m-%d")
    # print(tmp, type(tmp))
    try:
        file = open(r'D:\PDSSshare\redme.txt', 'r')
        raw = file.read()
        # print(t, type(t))
        file.close()
        if raw == tmp:
            print("OK")
        else:
            SendeMail()
    except Exception as e:
        print(e)
