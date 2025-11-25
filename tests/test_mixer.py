import copy
import unittest
from unittest import mock

import alsaaudio
import pytest
from mopidy import exceptions

from mopidy_alsamixer.mixer import AlsaMixer


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
        assert mixer.config is actual_config

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

        with pytest.raises(exceptions.MixerError) as exc_info:
            self.get_mixer(config=config)

        assert "Could not find ALSA device" in str(exc_info.value)
        assert "include: PCH, SB" in str(exc_info.value)

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

        with pytest.raises(exceptions.MixerError) as exc_info:
            self.get_mixer(config=config)

        assert "Could not find ALSA card" in str(exc_info.value)
        assert "include: PCH, SB" in str(exc_info.value)

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

        with pytest.raises(exceptions.MixerError) as exc_info:
            self.get_mixer(config=config)

        assert "Could not find ALSA mixer control" in str(exc_info.value)
        assert "include: Headphone, Master" in str(exc_info.value)

    def test_get_volume(self, alsa_mock):
        config = {"alsamixer": {"volume_scale": "linear"}}
        mixer = self.get_mixer(alsa_mock, config=config)
        mixer_mock = alsa_mock.Mixer.return_value
        mixer_mock.getvolume.return_value = [86]

        assert mixer.get_volume() == 86

        mixer_mock.getvolume.assert_called_once_with()

    def test_get_volume_cubic(self, alsa_mock):
        config = {"alsamixer": {"volume_scale": "cubic"}}
        mixer = self.get_mixer(alsa_mock, config=config)
        mixer_mock = alsa_mock.Mixer.return_value
        mixer_mock.getvolume.return_value = [86]

        assert mixer.get_volume() == 63

        mixer_mock.getvolume.assert_called_once_with()

    def test_get_volume_log(self, alsa_mock):
        config = {"alsamixer": {"volume_scale": "log"}}
        mixer = self.get_mixer(alsa_mock, config=config)
        mixer_mock = alsa_mock.Mixer.return_value
        mixer_mock.getvolume.return_value = [86]

        assert mixer.get_volume() == 52

        mixer_mock.getvolume.assert_called_once_with()

    def test_get_volume_when_channels_are_different(self, alsa_mock):
        mixer = self.get_mixer(alsa_mock)
        mixer_mock = alsa_mock.Mixer.return_value
        mixer_mock.getvolume.return_value = [86, 70]

        assert mixer.get_volume() is None

        mixer_mock.getvolume.assert_called_once_with()

    def test_get_volume_when_no_channels(self, alsa_mock):
        mixer = self.get_mixer(alsa_mock)
        mixer_mock = alsa_mock.Mixer.return_value
        mixer_mock.getvolume.return_value = []

        assert mixer.get_volume() is None

        mixer_mock.getvolume.assert_called_once_with()

    def test_set_volume(self, alsa_mock):
        config = {"alsamixer": {"volume_scale": "linear"}}
        mixer = self.get_mixer(alsa_mock, config=config)
        mixer_mock = alsa_mock.Mixer.return_value

        assert mixer.set_volume(74)

        mixer_mock.setvolume.assert_called_once_with(74)

    def test_set_volume_cubic(self, alsa_mock):
        config = {"alsamixer": {"volume_scale": "cubic"}}
        mixer = self.get_mixer(alsa_mock, config=config)
        mixer_mock = alsa_mock.Mixer.return_value

        assert mixer.set_volume(74)

        mixer_mock.setvolume.assert_called_once_with(90)

    def test_set_volume_log(self, alsa_mock):
        config = {"alsamixer": {"volume_scale": "log"}}
        mixer = self.get_mixer(alsa_mock, config=config)
        mixer_mock = alsa_mock.Mixer.return_value

        assert mixer.set_volume(74)

        mixer_mock.setvolume.assert_called_once_with(93)

    def test_get_mute_when_muted(self, alsa_mock):
        mixer = self.get_mixer(alsa_mock)
        mixer_mock = alsa_mock.Mixer.return_value
        mixer_mock.getmute.return_value = [1]

        assert mixer.get_mute() is True

        mixer_mock.getmute.assert_called_once_with()

    def test_get_mute_when_unmuted(self, alsa_mock):
        mixer = self.get_mixer(alsa_mock)
        mixer_mock = alsa_mock.Mixer.return_value
        mixer_mock.getmute.return_value = [0]

        assert mixer.get_mute() is False

        mixer_mock.getmute.assert_called_once_with()

    def test_get_mute_when_unsupported(self, alsa_mock):
        mixer = self.get_mixer(alsa_mock)
        mixer_mock = alsa_mock.Mixer.return_value
        mixer_mock.getmute.side_effect = alsa_mock.ALSAAudioError

        assert mixer.get_mute() is None

        mixer_mock.getmute.assert_called_once_with()

    def test_set_mute_to_muted(self, alsa_mock):
        mixer = self.get_mixer(alsa_mock)
        mixer_mock = alsa_mock.Mixer.return_value

        assert mixer.set_mute(True)

        mixer_mock.setmute.assert_called_once_with(1)

    def test_set_mute_when_unsupported(self, alsa_mock):
        mixer = self.get_mixer(alsa_mock)
        mixer_mock = alsa_mock.Mixer.return_value
        mixer_mock.setmute.side_effect = alsa_mock.ALSAAudioError

        assert not mixer.set_mute(True)

        mixer_mock.setmute.assert_called_once_with(1)

    def test_get_mute_when_channels_are_different(self, alsa_mock):
        mixer = self.get_mixer(alsa_mock)
        mixer_mock = alsa_mock.Mixer.return_value
        mixer_mock.getmute.return_value = [0, 1]

        assert mixer.get_mute() is None

        mixer_mock.getmute.assert_called_once_with()

    def test_set_mute_to_unmuted(self, alsa_mock):
        mixer = self.get_mixer(alsa_mock)
        mixer_mock = alsa_mock.Mixer.return_value

        assert mixer.set_mute(False)

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
        assert mixer.trigger_volume_changed.call_count == 0
        assert mixer.trigger_mute_changed.call_count == 0

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
