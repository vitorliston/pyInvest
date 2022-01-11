import PyInstaller.__main__
import os

#,'--noconsole'
param=[  '--name=%s' % 'PyInvest','--noconsole']#,  '--onefile','--icon=%s' % 'resources/icon.ico',]


for path, subdirs, files in os.walk('resources'):
    for name in files:
        if name.split('.')[-1] in ['ui','png','jpg','ico','json']:

            param.append('--add-data={};{}'.format(os.path.join(path, name),path))
#
#param.append('--version-file=%s' % 'version')
param.append('main.py')


PyInstaller.__main__.run(param)