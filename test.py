# coding   : utf-8 
# @Time    : 2020/3/10 16:41
# @Author  : 小迷弟
# @File    : test.py
# @Email   : lihu5682@126.com
# @Desc    : NONE
# @Software: PyCharm


import socket
import paramiko


def get_open():
    ssh  = paramiko.SSHClient()
    ssh.connect("192.162.129.175",username='lihu', password='5682jkljkl')
    print( ssh.exec_command("ipconfig"))


if __name__ == '__main__':
    get_open()