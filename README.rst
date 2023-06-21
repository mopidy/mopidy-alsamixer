****************
Mopidy-ALSAMixer
****************

.. image:: https://img.shields.io/pypi/v/Mopidy-ALSAMixer
    :target: https://pypi.python.org/pypi/Mopidy-ALSAMixer/
    :alt: Latest PyPI version

.. image:: https://img.shields.io/github/actions/workflow/status/mopidy/mopidy-alsamixer/ci.yml?branch=main
    :target: https://github.com/mopidy/mopidy-alsamixer/actions
    :alt: CI build status

.. image:: https://img.shields.io/codecov/c/gh/mopidy/mopidy-alsamixer
    :target: https://codecov.io/gh/mopidy/mopidy-alsamixer
    :alt: Test coverage

`Mopidy <https://www.mopidy.com/>`_ extension for ALSA volume control.


Maintainer wanted
=================

Mopidy-ALSAMixer is currently kept on life support by the Mopidy core developers.
It is in need of a more dedicated maintainer.

If you want to be the maintainer of Mopidy-ALSAMixer, please:

1. Make 2-3 good pull requests improving any part of the project.

2. Read and get familiar with all of the project's open issues.

3. Send a pull request removing this section and adding yourself as the
   "Current maintainer" in the "Credits" section below. In the pull request
   description, please refer to the previous pull requests and state that
   you've familiarized yourself with the open issues.

   As a maintainer, you'll be given push access to the repo and the authority
   to make releases to PyPI when you see fit.


Dependencies
============

- A Linux system using ALSA for audio playback.

- ``pyalsaaudio``. Bindings for using the ALSA API from Python. The package is
  available as ``python-alsaaudio`` in Debian/Ubuntu.


Installation
============

Install by running::

    sudo python3 -m pip install Mopidy-AlsaMixer

See https://mopidy.com/ext/alsamixer/ for alternative installation methods.


Configuration
=============

To use Mopidy-AlsaMixer the ``audio/mixer`` configuration value must be set to
``alsamixer`` in the Mopidy configuration file::

    [audio]
    mixer = alsamixer

The default Mopidy-AlsaMixer configuration will probably work for most use
cases. If not, the following configuration values are available:

- ``alsamixer/device``: Which soundcard should be used, specified by its string
  alias. Defaults to ``default``.

- ``alsamixer/card``: Which soundcard should be used, specified by its index.
  Numbered from 0 and up. If specified, ``alsamixer/device`` is ignored.

- ``alsamixer/control``: Which ALSA control should be used. Defaults to ``Master``.
  Other typical values includes ``PCM``. Run the command ``amixer scontrols``
  to list available controls on your system.

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
    min_volume = 0
    max_volume = 100
    volume_scale = cubic


Project resources
=================

- `Source code <https://github.com/mopidy/mopidy-alsamixer>`_
- `Issue tracker <https://github.com/mopidy/mopidy-alsamixer/issues>`_
- `Changelog <https://github.com/mopidy/mopidy-alsamixer/releases>`_


Credits
=======

- Original author: `Stein Magnus Jodal <https://github.com/jodal>`__
- Current maintainer: None. Maintainer wanted, see section above.
- `Contributors <https://github.com/mopidy/mopidy-alsamixer/graphs/contributors>`_
