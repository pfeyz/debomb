from distutils.core import setup

setup(name='debomb',
      version='0.1',
      author='Paul Feitzinger',
      author_email='paul@pfeyz.com',
      url='https://github.com/pfeyz/debomb',
      description='Clean up after tar/zip bomb explosions',
      py_modules=['debomber'],
      scripts=['debomb'],
      )
