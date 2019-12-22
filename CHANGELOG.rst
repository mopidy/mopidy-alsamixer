*********
Changelog
*********


v2.0.0 (2019-12-22)
===================

- Depend on final release of Mopidy 3.0.0.


v2.0.0rc1 (2019-11-11)
======================

- Require Mopidy >= 3.0.0a3.

- Require Python >= 3.7. No major changes required.

- Update project setup.


v1.1.1 (2018-04-01)
===================

- Require Mopidy >= 2.0, as we from release 1.1.0 import
  ``gi.repository.GstAudio``, which is incompatible with ``gobject`` which is
  used by Mopidy < 2.0.

- Don't rely on all cards which use a hardware card index to be included in the
  list returned by ``alsaaudio.cards()``. This can happen if an audio card is
  disabled, but still use up a "card index", for example when disabling the
  builtin audio card on a Raspberry Pi. (Fixes: #8)


v1.1.0 (2017-02-12)
===================

- Add ``alsamixer/min_volume`` and ``alsamixer/max_volume`` config values to
  make Mopidy-ALSAMixer's volume scale only use a part of the underlying ALSA
  volume scale. (PR: #9)

- Add ``alsamixer/volume_scale`` to allow switching between ``linear``,
  ``cubic``, and ``log`` scales. The default value has been changed from
  ``linear`` to ``cubic``, which is closer to how the human ear percieve the
  volume. (Fixes: #3, PR: #9)


v1.0.3 (2014-07-31)
===================

- Don't crash on epoll being interrupted by the machine suspending.


v1.0.2 (2014-07-27)
===================

- Handle mixer controls which does not support muting. (Fixes: #1)


v1.0.1 (2014-07-21)
===================

- Correctly require Mopidy 0.19 instead of 0.18.


v1.0.0 (2014-07-21)
===================

- Initial release.
