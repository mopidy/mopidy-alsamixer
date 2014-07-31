****************
Mopidy-ALSAMixer
****************

.. image:: https://img.shields.io/pypi/v/Mopidy-ALSAMixer.svg?style=flat
    :target: https://pypi.python.org/pypi/Mopidy-ALSAMixer/
    :alt: Latest PyPI version

.. image:: https://img.shields.io/pypi/dm/Mopidy-ALSAMixer.svg?style=flat
    :target: https://pypi.python.org/pypi/Mopidy-ALSAMixer/
    :alt: Number of PyPI downloads

.. image:: https://img.shields.io/travis/mopidy/mopidy-alsamixer/master.png?style=flat
    :target: https://travis-ci.org/mopidy/mopidy-alsamixer
    :alt: Travis CI build status

.. image:: https://img.shields.io/coveralls/mopidy/mopidy-alsamixer/master.svg?style=flat
   :target: https://coveralls.io/r/mopidy/mopidy-alsamixer?branch=master
   :alt: Test coverage

`Mopidy <http://www.mopidy.com/>`_ extension for ALSA volume control.


Dependencies
============

- A Linux system using ALSA for audio playback.

- ``pyalsaaudio``. Bindings for using the ALSA API from Python. The package is
  available as ``python-alsaaudio`` in Debian/Ubuntu.


Installation
============

Install by running::

    pip install Mopidy-ALSAMixer

Or, if available, install the Debian/Ubuntu package from `apt.mopidy.com
<http://apt.mopidy.com/>`_.


Configuration
=============

The default configuration will probably work for most use cases.

The following configuration values are available:

- ``alsamixer/card``: Which soundcard to use, if you have more than one.
  Numbered from 0 and up. 0 is the default.

- ``alsamixer/control``: Which ALSA control to use. Defaults to ``Master``.
  Other typical values includes ``PCM``. Run the command ``amixer scontrols``
  to list available controls on your system.

Example ``alsamixer`` section from the Mopidy configuration file::

    [alsamixer]
    card = 1
    control = PCM


Project resources
=================

- `Source code <https://github.com/mopidy/mopidy-alsamixer>`_
- `Issue tracker <https://github.com/mopidy/mopidy-alsamixer/issues>`_
- `Download development snapshot <https://github.com/mopidy/mopidy-alsamixer/archive/master.tar.gz#egg=Mopidy-ALSAMixer-dev>`_


Changelog
=========

v1.0.3 (2014-07-31)
-------------------

- Don't crash on epoll being interrupted by the machine suspending.

v1.0.2 (2014-07-27)
-------------------

- Handle mixer controls which does not support muting. (Fixes: #1)

v1.0.1 (2014-07-21)
-------------------

- Correctly require Mopidy 0.19 instead of 0.18.

v1.0.0 (2014-07-21)
-------------------

- Initial release.
