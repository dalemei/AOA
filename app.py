from flask import Flask
from flask import request, jsonify
from tools.ThirdModuleInstall import ThirdModule

app = Flask(__name__)


@app.route("/")
def hello():
    return "Hello world"


@app.route("/install_mysql/singleton", methods=['POST'])
def install_mysql_singleton():
    user = request.form.get("username")
    pwd = request.form.get('password')
    ip = request.form.get('ip')
    port = int(request.form.get('port') or '22')
    data_dir = request.form.get('datadir')
    print("%s,%s,%s,%s,%s" % (user, pwd, ip, port, data_dir))
    tm = ThirdModule(ip, port, user, pwd, data_dir)
    res = tm.install_mysql_node()
    print('res:', res)
    return "Hello world"


if __name__ == '__main__':
    app.run()
