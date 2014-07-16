from __future__ import unicode_literals

import logging
import select
import threading

import alsaaudio

from mopidy import exceptions, mixer

import pykka


logger = logging.getLogger(__name__)


class AlsaMixer(pykka.ThreadingActor, mixer.Mixer):

    name = 'alsamixer'

    def __init__(self, config):
        super(AlsaMixer, self).__init__()
        self.config = config
        self.card = self.config['alsamixer']['card']
        self.control = self.config['alsamixer']['control']

        known_cards = alsaaudio.cards()
        if self.card >= len(known_cards):
            raise exceptions.MixerError(
                'Could not find ALSA soundcard with index %(card)d. '
                'Known soundcards include: %(known_cards)s' % {
                    'card': self.card,
                    'known_cards': ', '.join(
                        '%d (%s)' % (i, name)
                        for i, name in enumerate(known_cards)),
                })

        known_controls = alsaaudio.mixers(self.card)
        if self.control not in known_controls:
            raise exceptions.MixerError(
                'Could not find ALSA mixer control %(control)s on '
                'card %(card)d. Known mixers on card %(card)d include: '
                '%(known_controls)s' % {
                    'control': self.control,
                    'card': self.card,
                    'known_controls': ', '.join(known_controls),
                })

        self._last_volume = None
        self._last_mute = None

        logger.info(
            'Mixing using ALSA, card %d, mixer control "%s".',
            self.card, self.control)

    def on_start(self):
        self._observer = AlsaMixerObserver(
            card=self.card, control=self.control,
            callback=self.actor_ref.proxy().trigger_events_for_changed_values)
        self._observer.start()

    @property
    def _mixer(self):
        # The mixer must be recreated every time it is used to be able to
        # observe volume/mute changes done by other applications.
        return alsaaudio.Mixer(control=self.control, cardindex=self.card)

    def get_volume(self):
        channels = self._mixer.getvolume()
        if not channels:
            return None
        elif channels.count(channels[0]) == len(channels):
            return int(channels[0])
        else:
            # Not all channels have the same volume
            return None

    def set_volume(self, volume):
        self._mixer.setvolume(volume)
        return True

    def get_mute(self):
        channels_muted = self._mixer.getmute()
        if all(channels_muted):
            return True
        elif not any(channels_muted):
            return False
        else:
            # Not all channels have the same mute state
            return None

    def set_mute(self, mute):
        self._mixer.setmute(int(mute))
        return True

    def trigger_events_for_changed_values(self):
        old_volume, self._last_volume = self._last_volume, self.get_volume()
        old_mute, self._last_mute = self._last_mute, self.get_mute()

        if old_volume != self._last_volume:
            self.trigger_volume_changed(self._last_volume)

        if old_mute != self._last_mute:
            self.trigger_mute_changed(self._last_mute)


class AlsaMixerObserver(threading.Thread):
    daemon = True
    name = 'AlsaMixerObserver'

    def __init__(self, card, control, callback=None):
        super(AlsaMixerObserver, self).__init__()
        self.running = True

        # Keep the mixer instance alive for the descriptors to work
        self.mixer = alsaaudio.Mixer(cardindex=card, control=control)
        descriptors = self.mixer.polldescriptors()
        assert len(descriptors) == 1
        self.fd = descriptors[0][0]
        self.event_mask = descriptors[0][1]

        self.callback = callback

    def stop(self):
        self.running = False

    def run(self):
        poller = select.epoll()
        poller.register(self.fd, self.event_mask | select.EPOLLET)
        while self.running:
            events = poller.poll(timeout=1)
            if events and self.callback is not None:
                self.callback()
