simplesms
=========

simplesms is a free/open source SMS/USSD gateway for building applications
that are based on basic short message service (SMS) and unstructured 
supplementary service data (USSD) mobile phone technology. It provides a
simple API for sending and handling incoming SMS, USSD responses and 'Flashing'
(phone calls that you do not intend to be picked up, instead to call attention) 


License
=======

simplesms is free software, available under the MIT License.


Prerequisites
=============

1) Python 2.6 - All development is done against Python 2.6.x
 
2) virtualenv - on Ubuntu please install python-virtualenv


Dependencies
============

* `pyserial <http://http://pyserial.sourceforge.net>`_
* `pytz <http://http://pytz.sourceforge.net>`_
* `pygsm <http://github.com/rapidsms/pygsm>`_
* `phonenumbers <http://pypi.python.org/pypi/phonenumbers>`_


Installing simplesms
====================

To setup an instance of simplesms in a clean virtualenv (named env)::

  $ virtualenv env --no-site-packages --python=python2.6
  $ source env/bin/activate
  $ pip install simplesms
  $ pip install pytz
  $ pip install git+git://github.com/eokyere/pygsm.git#egg=pygsm
	

Using simplesms
===============

To use simplesms, developers can subclass the simplesms.Handler class and 
implement the handle_sms, handle_call, and handle_ussd_response methods to 
handle incoming communications to their applications. Please look at the 
smsapp.py script in the demo folder.


Issues and submissions
=======================

Please note that the development status of this software is Alpha. Please file 
any bugs on the `github issue tracker`_, and/or submit a pull request.

.. _github issue tracker: http://github.com/eokyere/simplesms/issues


