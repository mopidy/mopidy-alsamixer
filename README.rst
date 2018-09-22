****************
Mopidy-ALSAMixer
****************

.. image:: https://img.shields.io/pypi/v/Mopidy-ALSAMixer.svg?style=flat
    :target: https://pypi.python.org/pypi/Mopidy-ALSAMixer/
    :alt: Latest PyPI version

.. image:: https://img.shields.io/travis/mopidy/mopidy-alsamixer/master.svg?style=flat
    :target: https://travis-ci.org/mopidy/mopidy-alsamixer
    :alt: Travis CI build status

.. image:: https://img.shields.io/coveralls/mopidy/mopidy-alsamixer/master.svg?style=flat
   :target: https://coveralls.io/r/mopidy/mopidy-alsamixer?branch=master
   :alt: Test coverage

`Mopidy <https://www.mopidy.com/>`_ extension for ALSA volume control.


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
<https://apt.mopidy.com/>`_.


Configuration
=============

The default configuration will probably work for most use cases.

The following configuration values are available:

- ``alsamixer/card``: Which soundcard to use, if you have more than one.
  Numbered from 0 and up. 0 is the default.

- ``alsamixer/control``: Which ALSA control to use. Defaults to ``Master``.
  Other typical values includes ``PCM``. Run the command ``amixer scontrols``
  to list available controls on your system.

- ``alsamixer/mixerid``: the id of the mixer control. Default is 0.

- ``alsamixer/min_volume`` and ``alsamixer/max_volume``: Map the Mopidy volume
  control range to a different range. Values are in the range 0-100. Use this
  if the default range (0-100) is too wide, resulting in a small usable range
  for Mopidy's volume control. For example try ``min_volume = 30`` and
  ``max_volume = 70`` to map Mopidy's volume control to the middle of ALSA's
  volume range.

- ``alsamixer/volume_scale``: Either ``linear``, ``cubic``, or ``log``. The
  cubic scale is the default as it is closer to how the human ear percieves
  volume, and matches the volume scale used in the ``alsamixer`` program.

Example ``alsamixer`` section from the Mopidy configuration file::

    [alsamixer]
    card = 1
    control = PCM
    mixerid = 0
    min_volume = 0
    max_volume = 100
    volume_scale = cubic

Project resources
=================

- `Source code <https://github.com/mopidy/mopidy-alsamixer>`_
- `Issue tracker <https://github.com/mopidy/mopidy-alsamixer/issues>`_


Credits
=======

- Original author: `Stein Magnus Jodal <https://github.com/jodal>`__
- Current maintainer: `Stein Magnus Jodal <https://github.com/jodal>`__
- `Contributors <https://github.com/mopidy/mopidy-alsamixer/graphs/contributors>`_


Changelog
=========

v1.1.1 (2018-04-01)
-------------------

- Require Mopidy >= 2.0, as we from release 1.1.0 import
  ``gi.repository.GstAudio``, which is incompatible with ``gobject`` which is
  used by Mopidy < 2.0.

- Don't rely on all cards which use a hardware card index to be included in the
  list returned by ``alsaaudio.cards()``. This can happen if an audio card is
  disabled, but still use up a "card index", for example when disabling the
  builtin audio card on a Raspberry Pi. (Fixes: #8)

v1.1.0 (2017-02-12)
-------------------

- Add ``alsamixer/min_volume`` and ``alsamixer/max_volume`` config values to
  make Mopidy-ALSAMixer's volume scale only use a part of the underlying ALSA
  volume scale. (PR: #9)

- Add ``alsamixer/volume_scale`` to allow switching between ``linear``,
  ``cubic``, and ``log`` scales. The default value has been changed from
  ``linear`` to ``cubic``, which is closer to how the human ear percieve the
  volume. (Fixes: #3, PR: #9)

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
