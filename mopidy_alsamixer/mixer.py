import logging
import math
import random
import select
import struct
import time

import alsaaudio
import gi
import pykka

gi.require_version("GstAudio", "1.0")  # noqa
from gi.repository import GstAudio  # noqa isort:skip

from mopidy import exceptions, mixer  # noqa isort:skip

from .polling_actor import PollingActor  # noqa

logger = logging.getLogger(__name__)


class AlsaMixer(pykka.ThreadingActor, mixer.Mixer):

    name = "alsamixer"

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.control = self.config["alsamixer"]["control"]
        self.device = self.config["alsamixer"]["device"]
        card = self.config["alsamixer"]["card"]
        self.min_volume = self.config["alsamixer"]["min_volume"]
        self.max_volume = self.config["alsamixer"]["max_volume"]
        self.volume_scale = self.config["alsamixer"]["volume_scale"]

        self.device_title = f"device {self.device!r}"
        if card is not None:
            self.device = f"hw:{card:d}"
            self.device_title = f"card {card:d}"

        known_cards = alsaaudio.cards()
        try:
            known_controls = alsaaudio.mixers(device=self.device)
        except alsaaudio.ALSAAudioError:
            raise exceptions.MixerError(
                f"Could not find ALSA {self.device_title}. "
                "Known soundcards include: "
                f"{', '.join(known_cards)}"
            )

        if self.control not in known_controls:
            raise exceptions.MixerError(
                "Could not find ALSA mixer control "
                f"{self.control} on {self.device_title}. "
                f"Known mixers on {self.device_title} include: "
                f"{', '.join(known_controls)}"
            )

        self._last_volume = None
        self._last_mute = None
        self._observer = None

        logger.info(
            f"Mixing using ALSA, {self.device_title}, "
            f"mixer control {self.control!r}."
        )

    def on_start(self):
        self._observer = AlsaMixerObserver.start(
            self._await_mixer(), self.actor_ref.proxy()
        )

    def on_stop(self):
        self._stop_observer()

    def on_failure(self, exception_type, exception_value, traceback):
        self._stop_observer()

    def restart_observer(self, exc=None):
        self._stop_observer()
        self._observer = AlsaMixerObserver.start(
            self._await_mixer(exc), self.actor_ref.proxy()
        )

    def _stop_observer(self):
        if self._observer is not None and self._observer.is_alive():
            self._observer.stop()

    @property
    def _mixer(self):
        # The mixer must be recreated every time it is used to be able to
        # observe volume/mute changes done by other applications.
        return alsaaudio.Mixer(
            device=self.device,
            control=self.control,
        )

    def _await_mixer(self, exc_0=None, sleep=True):
        while True:
            try:
                if exc_0 is not None:
                    exc, exc_0 = exc_0, None
                    raise exc

                return self._mixer

            except (alsaaudio.ALSAAudioError, OSError) as exc:
                logger.info(
                    f"Could not open ALSA {self.device_title}. "
                    "Retrying in a few seconds... "
                    f"Error: {exc}"
                )

                if sleep:
                    time.sleep(random.uniform(7, 10))

    def get_volume(self):
        try:
            channels = self._mixer.getvolume()
        except alsaaudio.ALSAAudioError:
            return None
        if not channels:
            return None
        elif channels.count(channels[0]) == len(channels):
            return self.mixer_volume_to_volume(channels[0])
        else:
            # Not all channels have the same volume
            return None

    def set_volume(self, volume):
        try:
            self._mixer.setvolume(self.volume_to_mixer_volume(volume))
        except alsaaudio.ALSAAudioError as exc:
            logger.debug(f"Setting volume failed: {exc}")
            return False
        return True

    def mixer_volume_to_volume(self, mixer_volume):
        volume = mixer_volume
        if self.volume_scale == "cubic":
            volume = (
                GstAudio.StreamVolume.convert_volume(
                    GstAudio.StreamVolumeFormat.CUBIC,
                    GstAudio.StreamVolumeFormat.LINEAR,
                    volume / 100.0,
                )
                * 100.0
            )
        elif self.volume_scale == "log":
            # Uses our own formula rather than GstAudio.StreamVolume.
            # convert_volume(GstAudio.StreamVolumeFormat.LINEAR,
            # GstAudio.StreamVolumeFormat.DB, mixer_volume / 100.0)
            # as the result is a DB value, which we can't work with as
            # self._mixer provides a percentage.
            volume = math.pow(10, volume / 50.0)
        volume = (
            (volume - self.min_volume)
            * 100.0
            / (self.max_volume - self.min_volume)
        )
        return int(volume)

    def volume_to_mixer_volume(self, volume):
        mixer_volume = (
            self.min_volume
            + volume * (self.max_volume - self.min_volume) / 100.0
        )
        if self.volume_scale == "cubic":
            mixer_volume = (
                GstAudio.StreamVolume.convert_volume(
                    GstAudio.StreamVolumeFormat.LINEAR,
                    GstAudio.StreamVolumeFormat.CUBIC,
                    mixer_volume / 100.0,
                )
                * 100.0
            )
        elif self.volume_scale == "log":
            # Uses our own formula rather than GstAudio.StreamVolume.
            # convert_volume(GstAudio.StreamVolumeFormat.LINEAR,
            # GstAudio.StreamVolumeFormat.DB, mixer_volume / 100.0)
            # as the result is a DB value, which we can't work with as
            # self._mixer wants a percentage.
            mixer_volume = 50 * math.log10(mixer_volume)
        return int(mixer_volume)

    def get_mute(self):
        try:
            channels_muted = self._mixer.getmute()
        except alsaaudio.ALSAAudioError:
            return None
        if all(channels_muted):
            return True
        elif not any(channels_muted):
            return False
        else:
            # Not all channels have the same mute state
            return None

    def set_mute(self, mute):
        try:
            self._mixer.setmute(int(mute))
            return True
        except alsaaudio.ALSAAudioError as exc:
            logger.debug(f"Setting mute state failed: {exc}")
            return False

    def trigger_events_for_changed_values(self):
        old_volume, self._last_volume = self._last_volume, self.get_volume()
        old_mute, self._last_mute = self._last_mute, self.get_mute()

        if old_volume != self._last_volume:
            self.trigger_volume_changed(self._last_volume)

        if old_mute != self._last_mute:
            self.trigger_mute_changed(self._last_mute)


class AlsaMixerObserver(PollingActor):

    name = "alsamixer-observer"

    combine_events = True

    def __init__(self, mixer, parent):
        # Note: ALSA mixer instance must be kept alive
        # to keep poll descriptors open
        self._mixer = mixer
        self._parent = parent

        # FIXME: Remove when a new version of pyalsaaudio is released
        # See https://github.com/larsimmisch/pyalsaaudio/pull/108
        def check_fd(fd):
            return fd != -1 and fd != struct.unpack("I", b"\xFF\xFF\xFF\xFF")[0]

        super().__init__(
            fds=tuple(
                (fd, event_mask | select.EPOLLET)
                for (fd, event_mask) in self._mixer.polldescriptors()
                if check_fd(fd)
            )
        )

    def on_start(self):
        logger.debug(
            f"Starting AlsaMixerObserver with {len(self._fds)} valid poll descriptors"
        )

    def on_failure(self, exception_type, exception_value, traceback):
        if exception_type is OSError:
            # OSError can normally occur after suspend/resume or device disconnection
            self._parent.restart_observer(exception_value)

    def on_poll(self, fd, event):
        if event & (select.EPOLLHUP | select.EPOLLERR):
            self._parent.restart_observer()
        else:
            self._parent.trigger_events_for_changed_values().get()
