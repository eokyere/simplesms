from distutils.core import setup

setup(name = 'simplesms',
      version = '0.1.3d',
      license = 'MIT',
      url = 'http://github.com/eokyere/simplesms',
      description = 'Build SMS apps on top of a simple SMS/USSD gateway',

      install_requires = [
          'phonenumbers==3.5b2',
          'pyserial'
      ],
      
      packages = ['simplesms', 'simplesms.contrib'],
      keywords = ['gsm', 'sms', 'communication'],

      classifiers = [
          'Development Status :: 3 - Alpha',
          'Environment :: Other Environment',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: MIT License',
          'Operating System :: OS Independent',
          'Programming Language :: Python'],
          
      long_description = open('README.txt', 'rt').read(),
      
      author = 'Emmanuel Okyere',
      author_email = 'chief@hutspace.net',
      )
