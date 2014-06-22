from __future__ import unicode_literals

import logging

from mopidy import mixer


logger = logging.getLogger(__name__)


class AlsaMixer(mixer.Mixer):
    pass
