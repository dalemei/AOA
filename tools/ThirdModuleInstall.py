import os
import configparser
import paramiko


class ThirdModule(object):
    """
    第三方模块功能由该模块完成，例如：
    安装数据库、redis等第三方组件
    """
    def __init__(self, ip=None, port=22, user=None, password=None, data_dir=None):
        """
        :param ip: ssh 连接 IP
        :param port: ssh 端口
        :param user: ssh 用户名
        :param password: ssh 端口
        :param data_dir: 存放数据地址
        """
        self.ip = ip
        self.port = port
        self.user = user
        self.password = password
        self.data_dir = data_dir

    def _connect(self):
        """
        使用paramiko远程连接初始化
        :return: sshclient:远程连接客户端
        """
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=self.ip, port=self.port, username=self.user, password=self.password)
        return ssh

    def _ip_2_server_id(self):
        """
        将传入的ip地址转化为server_id,避免server_id重复
        :return: server_id: ServerId值
        """
        m_list = [int(x) for x in self.ip.split(".")]
        m_str = ''
        for item in m_list:
            m_str += str(item)
        return m_str

    # scp mysql-8.0.19-linux-glibc2.12-x86_64.tar.xz to remote server
    def _scp_mysql_package(self):
        """
        将mysql安装包拷贝到远程服务器
        :return:
        """
        ssh = self._connect()
        transport = ssh.get_transport()
        sftp = paramiko.SFTPClient.from_transport(transport)
        mysql_package \
            = os.path.abspath(os.path.dirname(os.getcwd())) \
            + '/AOA/package/mysql-8.0.25-linux-glibc2.17-x86_64-minimal.tar.xz'
        sftp.put(mysql_package, '/usr/local/src/mysql-8.0.25-linux-glibc2.17-x86_64-minimal.tar.xz')
        ssh.close()
        sftp.close()

    # cd /usr/local/src
    # tar xf mysql-8.0.19-linux-glibc2.12-x86_64.tar.xz
    # mv mysql-8.0.19-linux-glibc2.12-x86_64 /usr/local/mysql8.0
    # echo 'export  PATH=/usr/local/mysql8.0/bin:$PATH' >> /etc/profile
    # . /etc/profile
    def _install_single_mysql(self):
        """
        安装mysql
        注意：由于paramiko会开启一个bash环境，所以将PATH添加到/etc/profile后，. /etc/profile该命令无法生效
        :return: 返回错误信息
        """
        command = "cd /usr/local/src && tar xf mysql-8.0.25-linux-glibc2.17-x86_64-minimal.tar.xz;" \
                  "cd /usr/local/src && mv mysql-8.0.25-linux-glibc2.17-x86_64-minimal /usr/local/mysql8.0;" \
                  "echo 'export  PATH=/usr/local/mysql8.0/bin:$PATH' >> /etc/profile;" \
                  ". /etc/profile"
        ssh = self._connect()
        stdin, stdout, stderr = ssh.exec_command(command)
        ssh.close()
        return stderr.read().decode('utf-8')

    # useradd -M -s /sbin/nologin mysql
    # mkdir -pv /datadir/{temp, log, data}
    # touch /datadir/log/err.log
    # chown -R mysql:mysql /datadir
    # mysqld --initialize-insecure --datadir=/datadir/data --user = mysql
    # chown -R mysql: mysql /datadir
    def _init_single_mysql(self):
        """
        初始化数据库
        :return: 返回初始化报错信息
        """
        command = "useradd -M -s /sbin/nologin mysql;" \
                  "mkdir -pv /%s/{temp,log,data};" \
                  "touch /%s/log/err.log;" \
                  "chown -R mysql:mysql /%s;" \
                  "/usr/local/mysql8.0/bin/mysqld --initialize-insecure --datadir=/%s/data --user=mysql;" \
                  "chown -R mysql:mysql /%s" % \
                  (self.data_dir, self.data_dir, self.data_dir, self.data_dir, self.data_dir)
        ssh = self._connect()
        stdin, stdout, stderr = ssh.exec_command(command)
        ssh.close()
        return stderr.read().decode('utf-8')

    # [mysqld]
    # basedir=/usr/local/mysql8.0
    # user=mysql
    # port=3306
    # mysqlx_port=33060
    # datadir=/datadir/data
    # log-error=/datadir/log/err.log
    # pid-file=/datadir/temp/mysqld.pid
    # socket=/datadir/temp/mysqld.sock
    # mysqlx_socket=/datadir/temp/mysqlx.sock
    # symbolic-links=0
    # server_id=36
    # gtid-mode=on
    # enforce-gtid-consistency=true
    # skip_ssl
    # log_bin=/datadir/log/binlog
    # binlog_format=ROW
    # secure_file_priv=''
    #
    # [client]
    # socket=/datadir/temp/mysqld.sock
    def _config_start_single_mysql(self):
        """
        配置文件生成，并安全启动数据库
        :return: 返回启动失败信息
        """
        config = configparser.ConfigParser()
        config['mysqld'] = {
            'basedir': '/usr/local/mysql8.0',
            'user': 'mysql',
            'port': '3306',
            'mysqlx_port': '33060',
            'datadir': '/%s/data' % (self.data_dir, ),
            'log-error': '/%s/log/err.log' % (self.data_dir, ),
            'pid-file': '/%s/temp/mysqld.pid' % (self.data_dir, ),
            'socket': '/%s/temp/mysqld.sock' % (self.data_dir, ),
            'mysqlx_socket': '/%s/temp/mysqlx.sock' % (self.data_dir, ),
            'symbolic-links': '0',
            'server_id': '%s' % self._ip_2_server_id(),
            'gtid-mode': 'on',
            'enforce-gtid-consistency': 'true',
            'skip_ssl': '1',
            'log_bin': '/%s/log/binlog' % (self.data_dir, ),
            'binlog_format': 'ROW',
            'secure_file_priv': '',
        }
        config['client'] ={
            'socket': '/%s/temp/mysqld.sock' % (self.data_dir, )
        }
        with open('my.cnf', 'w') as f:
            config.write(f)
        ssh = self._connect()
        transport = ssh.get_transport()
        sftp = paramiko.SFTPClient.from_transport(transport)
        sftp.put('my.cnf', '/etc/my.cnf')
        command = '/usr/local/mysql8.0/bin/mysqld_safe --defaults-file=/etc/my.cnf --daemonize'
        stdin, stdout, stderr = ssh.exec_command(command)
        sftp.close()
        ssh.close()
        return stderr.read().decode('utf-8')

    def _set_master_node(self):
        """
        将已经装好的数据库设置为master节点
        :return: 返回设置主节点失败信息
        """
        ssh = self._connect()
        command = "/usr/local/mysql8.0/bin/mysql -uroot -e " \
                  "\"CREATE USER 'repl'@'%' IDENTIFIED BY 'password';GRANT REPLICATION SLAVE ON *.* TO 'repl'@'%'\";"
        stdin, stdout, stderr = ssh.exec_command(command)
        ssh.close()
        return stderr.read().decode('utf-8')

    def _set_slave_node(self, m_ip):
        """
        将已经装好的数据库设置为slave节点
        :param m_ip: 主节点IP
        :return: 设置从节点报错信息
        """
        ssh = self._connect()
        command = "CHANGE MASTER TO MASTER_HOST = '%s'," \
                  "MASTER_PORT = 3306, " \
                  "MASTER_USER = 'repl', " \
                  "MASTER_PASSWORD = 'password', " \
                  "MASTER_AUTO_POSITION = 1;start slave;" % (m_ip, )
        stdin, stdout, stderr = ssh.exec_command(command)
        ssh.close()
        return stderr.read().decode('utf-8')

    def install_mysql_node(self):
        """
        将以上安装数据库的私有函数统一到该函数中，可对外提供单节点数据库的安装
        :return:
        """
        self._scp_mysql_package()
        res = self._install_single_mysql()
        if res != '':
            return res
        res = self._init_single_mysql()
        if res != '':
            return res
        res = self._config_start_single_mysql()
        if res != '':
            return res

    def install_master_mysql_node(self):
        res = self.install_mysql_node()
        if res != "":
            res = self._set_master_node()
        return res

    def install_slave_mysql_node(self, m_ip):
        res = self.install_mysql_node()
        if res != "":
            res = self._set_slave_node(m_ip)
        return res


if __name__ == '__main__':
    m = ThirdModule('192.168.3.128', 22, 'root', 'daleD1991', 'datadir')
    s = ThirdModule('192.168.3.129', 22, 'root', 'daleD1991', 'datadir')
    # tm.scp_mysql_package()
    # tm.install_single_mysql()
    # tm.init_single_mysql('datadir')
    # tm.config_start_single_mysql('datadir')
    # tm.set_master_node()
    m.install_master_mysql_node()
    s.install_slave_mysql_node(m.ip)
