# -*- coding: utf-8 -*-
"""
Created on Sun Mar  8 10:51:15 2020

@author: crxyy
"""
import time
from email import encoders
from email.header import Header
from email.mime.text import MIMEText
from email.utils import parseaddr, formataddr

def _format_addr(s):
    name, addr = parseaddr(s)
    return formataddr((Header(name, 'utf-8').encode(), addr))


#from_addr:发送地址，
#password:发送邮箱的密码.
#content: 邮件内容
#receive_email：收件人地址, 输入格式为["","",...]
def send_email(from_addr, password, content, receive_email):
    
    #正文
    msg = MIMEText(content, 'plain', 'utf-8')
    msg['From'] = _format_addr('基金行情监视器 <%s>' % from_addr)
    
    if len(receive_email) > 1:
        msg['To'] = ','.join(receive_email) #群发邮件
    else:
        msg['To'] = receive_email[0]
    
    subject_str = "基金行情:{0}"
    cur_time = time.strftime("Date[%m-%d] Time[%H:%M]", time.localtime())
    msg['Subject'] = Header(subject_str.format(cur_time), 'utf-8').encode()
    
    smtp_server = 'smtp.163.com' #SMTP服务器地址
    
    import smtplib
    #server = smtplib.SMTP(smtp_server, 465) # SMTP协议默认端口是25
    server = smtplib.SMTP_SSL(smtp_server, 465)# SMTP SSL协议默认端口是25
    server.set_debuglevel(1)
    server.login(from_addr, password)
    server.sendmail(from_addr, receive_email, msg.as_string())
    server.quit()