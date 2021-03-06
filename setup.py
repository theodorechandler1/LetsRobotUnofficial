import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name='letsrobot_unofficial',
    version='0.1.4',
    author='Theodore Chandler',
    author_email='theodorechandler1+LetsRobot@gmail.com',
    packages=['letsrobot_unofficial'],
    url='https://github.com/theodorechandler1/LetsRobotUnofficial',
    license='LICENSE.txt',
    description='Library to interface with LetsRobot',
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=[
        "socketIO-client",
    ],
)