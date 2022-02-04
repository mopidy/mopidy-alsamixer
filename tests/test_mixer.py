import contextlib
import copy
import errno
import os
import select
import threading
import time
import unittest
from unittest import mock

import alsaaudio
from mopidy import exceptions

from mopidy_alsamixer.mixer import AlsaMixer, AlsaMixerObserver
from mopidy_alsamixer.polling_actor import PollingActorInbox


@mock.patch(
    "mopidy_alsamixer.mixer.alsaaudio",
    spec=alsaaudio,
    ALSAAudioError=alsaaudio.ALSAAudioError,
)
class MixerTest(unittest.TestCase):

    default_config = {
        "alsamixer": {
            "device": "default",
            "card": None,
            "control": "Master",
            "min_volume": 0,
            "max_volume": 100,
            "volume_scale": "cubic",
        }
    }

    def get_mixer(self, alsa_mock=None, config=None, apply_default_config=True):
        if config is None:
            config = {"alsamixer": {"device": "default", "control": "Master"}}
        if alsa_mock is not None:
            alsa_mock.cards.return_value = ["PCH"]
            alsa_mock.mixers.return_value = ["Master"]
        if apply_default_config:
            actual_config = copy.deepcopy(MixerTest.default_config)
            actual_config["alsamixer"].update(config["alsamixer"])
        else:
            actual_config = config

        return AlsaMixer(config=actual_config)

    def test_has_config(self, alsa_mock):
        config = {"alsamixer": {"device": "default", "control": "Master"}}
        actual_config = copy.deepcopy(MixerTest.default_config)
        actual_config["alsamixer"].update(config["alsamixer"])

        mixer = self.get_mixer(
            alsa_mock, config=actual_config, apply_default_config=False
        )
        self.assertIs(mixer.config, actual_config)

    def test_use_default_device_from_config(self, alsa_mock):
        alsa_mock.cards.return_value = ["PCH", "SB"]
        alsa_mock.mixers.return_value = ["Master"]
        config = {"alsamixer": {"control": "Master"}}

        mixer = self.get_mixer(config=config)
        mixer.get_volume()

        alsa_mock.Mixer.assert_called_once_with(
            device="default",
            control="Master",
        )

    def test_use_device_from_config(self, alsa_mock):
        alsa_mock.cards.return_value = ["PCH", "SB"]
        alsa_mock.mixers.return_value = ["Master"]
        config = {
            "alsamixer": {
                "device": "PCH",
                "control": "Master",
            }
        }

        mixer = self.get_mixer(config=config)
        mixer.get_volume()

        alsa_mock.Mixer.assert_called_once_with(device="PCH", control="Master")

    def test_fails_if_device_is_unknown(self, alsa_mock):
        alsa_mock.cards.return_value = ["PCH", "SB"]
        alsa_mock.mixers.side_effect = alsa_mock.ALSAAudioError(
            "No such file or directory [PCH2]"
        )
        config = {"alsamixer": {"device": "PCH2", "control": "Master"}}

        with self.assertRaises(exceptions.MixerError) as ex:
            self.get_mixer(config=config)

        self.assertIn("Could not find ALSA device", str(ex.exception))
        self.assertIn("include: PCH, SB", str(ex.exception))

        alsa_mock.mixers.assert_called_once_with(device="PCH2")

    def test_use_card_from_config(self, alsa_mock):
        alsa_mock.cards.return_value = ["PCH", "SB"]
        alsa_mock.mixers.return_value = ["Master"]
        config = {"alsamixer": {"card": 1, "control": "Master"}}

        mixer = self.get_mixer(config=config)
        mixer.get_volume()

        alsa_mock.Mixer.assert_called_once_with(device="hw:1", control="Master")

    def test_use_card_with_index_not_in_cards_list(self, alsa_mock):
        alsa_mock.cards.return_value = ["PCH", "SB"]
        alsa_mock.mixers.return_value = ["Master"]
        config = {"alsamixer": {"card": 2, "control": "Master"}}

        mixer = self.get_mixer(config=config)
        mixer.get_volume()

        alsa_mock.mixers.assert_called_once_with(device="hw:2")
        alsa_mock.Mixer.assert_called_once_with(device="hw:2", control="Master")

    def test_fails_if_card_is_unknown(self, alsa_mock):
        alsa_mock.cards.return_value = ["PCH", "SB"]
        alsa_mock.mixers.side_effect = alsa_mock.ALSAAudioError(
            "No such file or directory [hw:2]"
        )
        config = {"alsamixer": {"card": 2, "control": "Master"}}

        with self.assertRaises(exceptions.MixerError) as ex:
            self.get_mixer(config=config)

        self.assertIn("Could not find ALSA card", str(ex.exception))
        self.assertIn("include: PCH, SB", str(ex.exception))

        alsa_mock.mixers.assert_called_once_with(device="hw:2")

    def test_use_control_from_config(self, alsa_mock):
        alsa_mock.cards.return_value = ["PCH", "SB"]
        alsa_mock.mixers.return_value = ["Speaker"]
        config = {"alsamixer": {"device": "PCH", "control": "Speaker"}}
        mixer = self.get_mixer(config=config)

        mixer.get_volume()

        alsa_mock.Mixer.assert_called_once_with(device="PCH", control="Speaker")

    def test_fails_if_control_is_unknown(self, alsa_mock):
        alsa_mock.cards.return_value = ["PCH", "SB"]
        alsa_mock.mixers.return_value = ["Headphone", "Master"]
        config = {"alsamixer": {"device": "PCH", "control": "Speaker"}}

        with self.assertRaises(exceptions.MixerError) as ex:
            self.get_mixer(config=config)

        self.assertIn("Could not find ALSA mixer control", str(ex.exception))
        self.assertIn("include: Headphone, Master", str(ex.exception))

    def test_get_volume(self, alsa_mock):
        config = {"alsamixer": {"volume_scale": "linear"}}
        mixer = self.get_mixer(alsa_mock, config=config)
        mixer_mock = alsa_mock.Mixer.return_value
        mixer_mock.getvolume.return_value = [86]

        self.assertEqual(mixer.get_volume(), 86)

        mixer_mock.getvolume.assert_called_once_with()

    def test_get_volume_cubic(self, alsa_mock):
        config = {"alsamixer": {"volume_scale": "cubic"}}
        mixer = self.get_mixer(alsa_mock, config=config)
        mixer_mock = alsa_mock.Mixer.return_value
        mixer_mock.getvolume.return_value = [86]

        self.assertEqual(mixer.get_volume(), 63)

        mixer_mock.getvolume.assert_called_once_with()

    def test_get_volume_log(self, alsa_mock):
        config = {"alsamixer": {"volume_scale": "log"}}
        mixer = self.get_mixer(alsa_mock, config=config)
        mixer_mock = alsa_mock.Mixer.return_value
        mixer_mock.getvolume.return_value = [86]

        self.assertEqual(mixer.get_volume(), 52)

        mixer_mock.getvolume.assert_called_once_with()

    def test_get_volume_when_channels_are_different(self, alsa_mock):
        mixer = self.get_mixer(alsa_mock)
        mixer_mock = alsa_mock.Mixer.return_value
        mixer_mock.getvolume.return_value = [86, 70]

        self.assertIsNone(mixer.get_volume())

        mixer_mock.getvolume.assert_called_once_with()

    def test_get_volume_when_no_channels(self, alsa_mock):
        mixer = self.get_mixer(alsa_mock)
        mixer_mock = alsa_mock.Mixer.return_value
        mixer_mock.getvolume.return_value = []

        self.assertIsNone(mixer.get_volume())

        mixer_mock.getvolume.assert_called_once_with()

    def test_get_volume_when_unavailable(self, alsa_mock):
        mixer = self.get_mixer(alsa_mock)
        alsa_mock.Mixer.side_effect = alsaaudio.ALSAAudioError

        self.assertIsNone(mixer.get_volume())

    def test_set_volume(self, alsa_mock):
        config = {"alsamixer": {"volume_scale": "linear"}}
        mixer = self.get_mixer(alsa_mock, config=config)
        mixer_mock = alsa_mock.Mixer.return_value

        self.assertTrue(mixer.set_volume(74))

        mixer_mock.setvolume.assert_called_once_with(74)

    def test_set_volume_cubic(self, alsa_mock):
        config = {"alsamixer": {"volume_scale": "cubic"}}
        mixer = self.get_mixer(alsa_mock, config=config)
        mixer_mock = alsa_mock.Mixer.return_value

        self.assertTrue(mixer.set_volume(74))

        mixer_mock.setvolume.assert_called_once_with(90)

    def test_set_volume_log(self, alsa_mock):
        config = {"alsamixer": {"volume_scale": "log"}}
        mixer = self.get_mixer(alsa_mock, config=config)
        mixer_mock = alsa_mock.Mixer.return_value

        self.assertTrue(mixer.set_volume(74))

        mixer_mock.setvolume.assert_called_once_with(93)

    def test_set_volume_when_unavailable(self, alsa_mock):
        mixer = self.get_mixer(alsa_mock)
        alsa_mock.Mixer.side_effect = alsaaudio.ALSAAudioError

        self.assertIs(mixer.set_volume(74), False)

    def test_get_mute_when_muted(self, alsa_mock):
        mixer = self.get_mixer(alsa_mock)
        mixer_mock = alsa_mock.Mixer.return_value
        mixer_mock.getmute.return_value = [1]

        self.assertIs(mixer.get_mute(), True)

        mixer_mock.getmute.assert_called_once_with()

    def test_get_mute_when_unmuted(self, alsa_mock):
        mixer = self.get_mixer(alsa_mock)
        mixer_mock = alsa_mock.Mixer.return_value
        mixer_mock.getmute.return_value = [0]

        self.assertIs(mixer.get_mute(), False)

        mixer_mock.getmute.assert_called_once_with()

    def test_get_mute_when_unsupported(self, alsa_mock):
        mixer = self.get_mixer(alsa_mock)
        mixer_mock = alsa_mock.Mixer.return_value
        mixer_mock.getmute.side_effect = alsa_mock.ALSAAudioError

        self.assertIsNone(mixer.get_mute())

        mixer_mock.getmute.assert_called_once_with()

    def test_set_mute_to_muted(self, alsa_mock):
        mixer = self.get_mixer(alsa_mock)
        mixer_mock = alsa_mock.Mixer.return_value

        self.assertTrue(mixer.set_mute(True))

        mixer_mock.setmute.assert_called_once_with(1)

    def test_set_mute_when_unsupported(self, alsa_mock):
        mixer = self.get_mixer(alsa_mock)
        mixer_mock = alsa_mock.Mixer.return_value
        mixer_mock.setmute.side_effect = alsa_mock.ALSAAudioError

        self.assertFalse(mixer.set_mute(True))

        mixer_mock.setmute.assert_called_once_with(1)

    def test_get_mute_when_channels_are_different(self, alsa_mock):
        mixer = self.get_mixer(alsa_mock)
        mixer_mock = alsa_mock.Mixer.return_value
        mixer_mock.getmute.return_value = [0, 1]

        self.assertIs(mixer.get_mute(), None)

        mixer_mock.getmute.assert_called_once_with()

    def test_set_mute_to_unmuted(self, alsa_mock):
        mixer = self.get_mixer(alsa_mock)
        mixer_mock = alsa_mock.Mixer.return_value

        self.assertTrue(mixer.set_mute(False))

        mixer_mock.setmute.assert_called_once_with(0)

    def test_trigger_events_for_changed_values_when_no_change(self, alsa_mock):
        mixer_mock = alsa_mock.Mixer.return_value
        mixer_mock.getvolume.return_value = [70]
        mixer_mock.getmute.return_value = [0]
        mixer = self.get_mixer(alsa_mock)
        mixer.trigger_volume_changed = mock.Mock()
        mixer.trigger_mute_changed = mock.Mock()

        mixer.trigger_events_for_changed_values()
        alsa_mock.reset_mock()
        mixer.trigger_volume_changed.reset_mock()
        mixer.trigger_mute_changed.reset_mock()

        mixer.trigger_events_for_changed_values()

        mixer_mock.getvolume.assert_called_once_with()
        mixer_mock.getmute.assert_called_once_with()
        self.assertEqual(mixer.trigger_volume_changed.call_count, 0)
        self.assertEqual(mixer.trigger_mute_changed.call_count, 0)

    def test_trigger_events_for_changed_values_when_changes(self, alsa_mock):
        mixer_mock = alsa_mock.Mixer.return_value
        mixer_mock.getvolume.return_value = [75]
        mixer_mock.getmute.return_value = [1]
        config = {"alsamixer": {"volume_scale": "linear"}}
        mixer = self.get_mixer(alsa_mock, config=config)
        mixer.trigger_volume_changed = mock.Mock()
        mixer.trigger_mute_changed = mock.Mock()

        mixer.trigger_events_for_changed_values()

        mixer_mock.getvolume.assert_called_once_with()
        mixer_mock.getmute.assert_called_once_with()
        mixer.trigger_volume_changed.assert_called_once_with(75)
        mixer.trigger_mute_changed.assert_called_once_with(True)

    def test_await_mixer(self, alsa_mock):
        mixer_mock = mock.Mock()
        mixer = self.get_mixer(alsa_mock)

        alsa_mock.Mixer.side_effect = (alsa_mock.ALSAAudioError(""), mixer_mock)
        self.assertEqual(mixer._await_mixer(sleep=False), mixer_mock)
        self.assertEqual(alsa_mock.Mixer.call_count, 2)
        alsa_mock.Mixer.reset_mock()

        alsa_mock.Mixer.side_effect = (alsa_mock.ALSAAudioError(""), mixer_mock)
        self.assertEqual(
            mixer._await_mixer(OSError(errno.EBADF), sleep=False),
            mixer_mock,
        )
        self.assertEqual(alsa_mock.Mixer.call_count, 2)


@mock.patch(
    "mopidy_alsamixer.mixer.AlsaMixer",
    spec=AlsaMixer,
)
class ObserverTest(unittest.TestCase):
    @contextlib.contextmanager
    def running_observer(self, mixer_mock, parent_mock):
        event = threading.Event()

        def side_effect(*args):
            event.set()
            return mock.Mock()(*args)

        parent_mock.trigger_events_for_changed_values.side_effect = side_effect
        parent_mock.restart_observer.side_effect = side_effect

        observer = AlsaMixerObserver.start(mixer_mock, parent_mock)
        yield observer

        event.wait()
        observer.stop()

    @contextlib.contextmanager
    def pipes(self, n, close=True):
        fds = tuple(os.pipe() for i in range(n))
        yield fds

        if close:
            for rfd, wfd in fds:
                os.close(rfd)
                os.close(wfd)

    def test_multiple_fd_multiple_events(self, parent_mock):
        mixer_mock = mock.Mock()

        with self.pipes(3) as fds:
            mixer_mock.polldescriptors.return_value = (
                (fds[0][0], select.EPOLLOUT),
                (fds[1][0], select.EPOLLIN),
                (fds[2][0], select.EPOLLIN | select.EPOLLOUT | select.EPOLLPRI),
            )

            with self.running_observer(mixer_mock, parent_mock):
                os.write(fds[1][1], b"\xFF")
                time.sleep(1)
                os.write(fds[1][1], b"\xFF")
                os.write(fds[2][1], b"\xFF")
                time.sleep(1)
                os.write(fds[0][1], b"\xFF")  # Should be ignored
                time.sleep(1)
                os.write(fds[1][1], b"\xFF")
                time.sleep(1)

        mixer_mock.polldescriptors.assert_called_once_with()
        self.assertEqual(
            parent_mock.trigger_events_for_changed_values.call_count, 3
        )
        parent_mock.restart_observer.assert_not_called()

    def test_mixer_disconnect(self, parent_mock):
        mixer_mock = mock.Mock()

        with self.pipes(1, False) as fds:
            mixer_mock.polldescriptors.return_value = (
                (
                    fds[0][1],
                    select.EPOLLIN,
                ),  # Note that we pass write end of the pipe
            )

            with self.running_observer(mixer_mock, parent_mock):
                os.close(
                    fds[0][0]
                )  # Closing read end of the pipe triggers EPOLLERR

        mixer_mock.polldescriptors.assert_called_once_with()
        parent_mock.restart_observer.assert_called_once()
        parent_mock.trigger_events_for_changed_values.assert_not_called()

    def test_poll_exception(self, parent_mock):
        mixer_mock = mock.Mock()
        mixer_mock.polldescriptors.return_value = tuple()

        with self.running_observer(mixer_mock, parent_mock) as observer:
            observer._actor._poll = mock.Mock()
            observer._actor._poll.poll.side_effect = OSError

            observer._actor._wake()
            time.sleep(1)

        parent_mock.restart_observer.assert_called_once()
        parent_mock.trigger_events_for_changed_values.assert_not_called()

    def test_combine_filter(self, parent_mock):
        combiner = PollingActorInbox._combine_filter()

        x = (
            (0, select.EPOLLERR),
            (1, select.EPOLLERR),
            (0, select.EPOLLIN),
            (1, select.EPOLLOUT),
            (0, select.EPOLLERR),
            (1, select.EPOLLIN | select.EPOLLERR),
            (0, select.EPOLLIN),
            (1, select.EPOLLHUP),
        )

        y = (
            (0, select.EPOLLERR),
            (1, select.EPOLLERR),
            (0, select.EPOLLIN),
            (0, select.EPOLLERR),
            (1, select.EPOLLIN | select.EPOLLERR),
            (1, select.EPOLLHUP),
        )

        self.assertEqual(tuple(filter(combiner, x)), y)
