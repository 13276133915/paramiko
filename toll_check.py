# coding   : utf-8 
# @Time    : 2020/3/10 15:00
# @Author  : 小迷弟
# @File    : toll_check.py
# @Email   : lihu5682@126.com
# @Desc    : NONE
# @Software: PyCharm
# coding:utf-8


import socket
from concurrent.futures import ThreadPoolExecutor as Pool
import paramiko
import mysql.connector
import select
import socks
from mysql.connector import ProgrammingError





def do_socket_find_toll():
    # 扫描范围,添加新IP,'新IP,这里是IP的前三位'
    # all_range = ['10.34.22'] #Wu Zhuang
    all_range = ['10.134.35']   #Chu Zhou Dong
    # 默认0
    range_start = 0
    # 默认255
    range_end = 255
    core_max_workers = 200
    find_result = []
    find_ips = []
    pool = Pool(max_workers=core_max_workers)
    for ip_statement in all_range:
        for find_ip in range(range_start, range_end):
            find_ips.append("{}.{}".format(ip_statement, find_ip))
    find_sum = len(find_ips)
    find_success = 0
    find_error = 0
    print("scan length:{}".format(find_sum))
    for result in pool.map(connect_toll, find_ips):
        if result is not None:
            find_success += 1
            find_result.append(result)
        else:
            find_error += 1
    print("需要扫描:{}个IP".format(find_sum))
    print("有效IP:{}个".format(find_success))
    print("无效IP:{}个".format(find_error))
    return find_result


def connect_toll(find_ip):
    port = 8491
    timeout = 2000
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.settimeout(timeout)
        client.connect((find_ip, port))
        # client.send('{"MessageType":"Request_Version"}'.encode('utf-8'))
        # for i in range(1, 14096):
        #     client.send('  '.encode())
        # data = client.recv(1024).decode()  # receive response
        # print('Received from server: ' + data)  # show in terminal
        # client.close()
        # TODO search version
        return find_ip
    except OSError as e:
        return None


def do_ssh_check(find_result):
    for ip in find_result:
        print("当前正在处理:{}".format(ip))
        transport = paramiko.Transport((ip, 22))
        transport.connect(username='root', password='wtkjsys1')
        check_database(ip)
        ssh = paramiko.SSHClient()
        ssh._transport = transport
        # check_net(ssh)
        check_config(ssh)
        check_sys(ssh)
        check_wait_update_list(ssh)
        transport.close()


def check_wait_update_list(ssh):
    print("检查未升级的程序:")
    stdin, stdout, stderr = ssh.exec_command('ll /wtlane/update | grep zip')
    print(str(stdout.channel.recv(1024), encoding='utf-8'))


def check_sys(ssh):
    print('检查车道时间:')
    stdin, stdout, stderr = ssh.exec_command('date -R')
    print(str(stdout.channel.recv(1024), encoding='utf-8'))


def check_config(ssh):
    print('正在检查:/wtlane/tc/resources/config.properties')
    stdin, stdout, stderr = ssh.exec_command('cat /wtlane/tc/resources/config.properties | grep switch.time')
    print(str(stdout.channel.recv(1024), encoding='utf-8'))
    stdin, stdout, stderr = ssh.exec_command('cat /wtlane/tc_switch/resources/config.properties | grep switch.time')
    print(str(stdout.channel.recv(1024), encoding='utf-8'))
    print('如果显示:请检查切换时间正确')
    print('正在检查:/wtlane/tc/resources/database.properties')
    stdin, stdout, stderr = ssh.exec_command('cat /wtlane/tc/resources/database.properties | grep ds.jdbcUrl')
    print(str(stdout.channel.recv(1024), encoding='utf-8'))
    stdin, stdout, stderr = ssh.exec_command('cat /wtlane/tc_switch/resources/database.properties | grep ds.jdbcUrl')
    print(str(stdout.channel.recv(1024), encoding='utf-8'))
    print('检查数据库收费数据库地址是否正确')
    print('正在检查:/wtlane/tc/resources/external.properties')
    stdin, stdout, stderr = ssh.exec_command(
        'cat /wtlane/tc/resources/external.properties | grep -E \'nameListHostAddress|tollMonitorAddressAfterSwitch\'')
    print(str(stdout.channel.recv(1024), encoding='utf-8'))
    stdin, stdout, stderr = ssh.exec_command(
        'cat /wtlane/tc_switch/resources/external.properties | grep -E \'nameListHostAddress|tollMonitorAddressAfterSwitch\'')
    print(str(stdout.channel.recv(1024), encoding='utf-8'))
    print('检测名单和监控地址是否正确')
    print('正在检查:/wtlane/tc/resources/gantry.properties')
    stdin, stdout, stderr = ssh.exec_command('cat /wtlane/tc/resources/gantry.properties | grep -v \'#\'')
    print(str(stdout.channel.recv(1024), encoding='utf-8'))
    stdin, stdout, stderr = ssh.exec_command('cat /wtlane/tc_switch/resources/gantry.properties | grep -v \'#\'')
    print(str(stdout.channel.recv(1024), encoding='utf-8'))
    print('检查门架开关:没有这个文件,或内容为空,则忽略')


def check_net(ssh):
    print('检查7.161网络连通性')
    stdin, stdout, stderr = ssh.exec_command('ping -w 5 10.134.7.161')
    print_stdout(stdout)
    print('检查7.161接口访问')
    stdin, stdout, stderr = ssh.exec_command('wget --timeout=3 --waitretry=2 --tries=3 https://10.134.7.161:443 --no-check-certificate')
    print_stderr(stderr)
    print('检查7.166网络连通性')
    stdin, stdout, stderr = ssh.exec_command('ping -w 5 10.134.7.166')
    print_stdout(stdout)
    print('检查7.166接口访问')
    stdin, stdout, stderr = ssh.exec_command('wget --timeout=3 --waitretry=2 --tries=3 https://10.134.7.166:443 --no-check-certificate')
    print_stderr(stderr)


def check_database(ip):
    conn = mysql.connector.connect(host=ip, user='dbuser1', password='wtkjdb1', database='system')
    try:
        cur = conn.cursor()
        sql1 = 'SELECT * FROM system.mc_allroadinfo_version'
        print("检查最短路径费率版本表:{}:".format(sql1))
        cur.execute(sql1)
        print_sql_result(cur.fetchall())
    except ProgrammingError as e:
        print('检查最短路径费率版本表失败')

    try:
        sql2 = 'SELECT count(*),Version FROM system.mc_allroadinfo group by Version'
        print("检查最短路径费率:{}:".format(sql2))
        cur.execute(sql2)
        print_sql_result(cur.fetchall())
    except ProgrammingError as e:
        print('检查最短路径费率失败')

    try:
        sql3 = 'SELECT count(*),version FROM system.mc_ygzcode group by version'
        print("检查全网收费站编码:{}:".format(sql3))
        cur.execute(sql3)
        print_sql_result(cur.fetchall())
    except ProgrammingError as e:
        print('检查全网收费站编码失败')


def print_sql_result(listall):
    for sql_result in listall:
        print(sql_result)


def print_stdout(stdout):
    while not stdout.channel.exit_status_ready():
        if stdout.channel.recv_ready():
            rl, wl, xl = select.select([stdout.channel], [], [], 0.0)
            if len(rl) > 0:
                print(str(stdout.channel.recv(1024), encoding='utf-8'))


def print_stderr(stderr):
    out = stderr.readlines()
    # print
    for o in out:
        print(o)


if __name__ == '__main__':
    socks.set_default_proxy(socks.SOCKS5, "192.162.123.161", 2112)
    socket.socket = socks.socksocket
    find_result = do_socket_find_toll()
    do_ssh_check(find_result)
