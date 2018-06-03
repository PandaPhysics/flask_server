from os import system, path
from flask import request, Flask
basedir = '/home/snarayan/doxy/repos/'
app = Flask('doxy')

@app.route('/push', methods=['POST'])
def push():
    data = request.get_json()
    repo = data['repository']['git_url'].split('/')[-1].replace('.git','')
    if not path.isdir(basedir+repo):
        system('cd %s; git lfs clone %s %s'%(basedir, data['repository']['clone_url'], repo))
    system('cd %s/%s ; git pull origin master'%(basedir,repo))
    system('cd %s ; doxygen ../doxy.cfg'%basedir)
    return 'Success!'

