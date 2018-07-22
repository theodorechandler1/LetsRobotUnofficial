from distutils.core import setup

setup(
    name='LetsRobot',
    version='0.1.0',
    author='Theodore Chandler',
    author_email='theodorechandler1+LetsRobot@gmail.com',
    packages=['letsrobot_unofficial'],
    url='http://pypi.python.org/pypi/LetsRobot/',
    license='LICENSE.txt',
    description='Library to interface with LetsRobot',
    long_description=open('README.txt').read(),
    install_requires=[
        "socketIO-client",
    ],
)