import os
import configparser
import paramiko


class ThirdModule(object):
    def __init__(self, ip=None, port=22, user=None, password=None):
        self.ip = ip
        self.port = port
        self.user = user
        self.password = password

    def _connect(self):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=self.ip, port=self.port, username=self.user, password=self.password)
        return ssh

    def _ip_2_server_id(self):
        m_list = [int(x) for x in self.ip.split(".")]
        m_str = ''
        for item in m_list:
            m_str += str(item)
        return m_str

    # scp mysql-8.0.19-linux-glibc2.12-x86_64.tar.xz to remote server
    def scp_mysql_package(self):
        ssh = self._connect()
        transport = ssh.get_transport()
        sftp = paramiko.SFTPClient.from_transport(transport)
        mysql_package \
            = os.path.abspath(os.path.dirname(os.getcwd())) \
            + '/package/mysql-8.0.25-linux-glibc2.17-x86_64-minimal.tar.xz'
        sftp.put(mysql_package, '/usr/local/src/mysql-8.0.25-linux-glibc2.17-x86_64-minimal.tar.xz')
        ssh.close()
        sftp.close()

    # cd /usr/local/src
    # tar xf mysql-8.0.19-linux-glibc2.12-x86_64.tar.xz
    # mv mysql-8.0.19-linux-glibc2.12-x86_64 /usr/local/mysql8.0
    # echo 'export  PATH=/usr/local/mysql8.0/bin:$PATH' >> /etc/profile
    # . /etc/profile
    def install_single_mysql(self):
        command = "cd /usr/local/src && tar xf mysql-8.0.25-linux-glibc2.17-x86_64-minimal.tar.xz;" \
                  "cd /usr/local/src && mv mysql-8.0.25-linux-glibc2.17-x86_64-minimal /usr/local/mysql8.0;" \
                  "echo 'export  PATH=/usr/local/mysql8.0/bin:$PATH' >> /etc/profile;" \
                  ". /etc/profile"
        # command = ". /etc/profile"
        ssh = self._connect()
        stdin, stdout, stderr = ssh.exec_command(command)
        print(stderr.read())
        ssh.close()

    # useradd -M -s /sbin/nologin mysql
    # mkdir -pv /datadir/{temp, log, data}
    # touch /datadir/log/err.log
    # chown -R mysql:mysql /datadir
    # mysqld --initialize-insecure --datadir=/datadir/data --user = mysql
    # chown -R mysql: mysql /datadir
    def init_single_mysql(self, data_dir):
        command = "useradd -M -s /sbin/nologin mysql;" \
                  "mkdir -pv /%s/{temp,log,data};" \
                  "touch /%s/log/err.log;" \
                  "chown -R mysql:mysql /%s;" \
                  "/usr/local/mysql8.0/bin/mysqld --initialize-insecure --datadir=/%s/data --user=mysql;" \
                  "chown -R mysql:mysql /%s" % (data_dir, data_dir, data_dir, data_dir, data_dir)
        ssh = self._connect()
        stdin, stdout, stderr = ssh.exec_command(command)
        print(stderr.read())
        ssh.close()

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
    def config_start_single_mysql(self, data_dir):
        config = configparser.ConfigParser()
        config['mysqld'] = {
            'basedir': '/usr/local/mysql8.0',
            'user': 'mysql',
            'port': '3306',
            'mysqlx_port': '33060',
            'datadir': '/%s/data' % (data_dir, ),
            'log-error': '/%s/log/err.log' % (data_dir, ),
            'pid-file': '/%s/temp/mysqld.pid' % (data_dir, ),
            'socket': '/%s/temp/mysqld.sock' % (data_dir, ),
            'mysqlx_socket': '/%s/temp/mysqlx.sock' % (data_dir, ),
            'symbolic-links': '0',
            'server_id': '%s' % self._ip_2_server_id(),
            'gtid-mode': 'on',
            'enforce-gtid-consistency': 'true',
            'skip_ssl': '1',
            'log_bin': '/%s/log/binlog' % (data_dir, ),
            'binlog_format': 'ROW',
            'secure_file_priv': '',
        }
        config['client'] ={
            'socket': '/%s/temp/mysqld.sock' % (data_dir, )
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
        print(stderr.read())

    def set_master_node(self):
        ssh = self._connect()
        command = "mysql -uroot -e CREATE USER 'repl'@'%' IDENTIFIED BY 'password';" \
                  "mysql -uroot -e GRANT REPLICATION SLAVE ON *.* TO 'repl'@'%';"
        ssh.exec_command(command)
        ssh.close()

    def set_slave_node(self):
        pass


if __name__ == '__main__':
    tm = ThirdModule('192.168.3.128', 22, 'root', 'daleD1991')
    tm.scp_mysql_package()
    tm.install_single_mysql()
    tm.init_single_mysql('datadir')
    tm.config_start_single_mysql('datadir')
