from flask import Flask
from flask import request
from tools.ThirdModuleInstall import ThirdModule

app = Flask(__name__)


@app.route("/")
def hello():
    return "Hello world"


@app.route("/install_mysql/singleton", methods=['Get', 'POST'])
def install_mysql_singleton():
    user = request.form['username']
    pwd = request.form['password']
    ip = request.form['ip']
    port = request.form['port'] or '3306'
    tm = ThirdModule(ip, port, user, pwd)
    tm.scp_mysql_package()


if __name__ == '__main__':
    app.run()
