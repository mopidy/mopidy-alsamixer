import logging
import os
import queue
import select
import sys
from typing import Any, NamedTuple, Tuple

import pykka
import pykka._envelope
import pykka.messages

logger = logging.getLogger(__name__)


class PollingActor(pykka.ThreadingActor):

    combine_events = False

    def __init__(self, fds=tuple()):
        super().__init__()

        self._fds = fds
        self._poll = None

    def _start_actor_loop(self):
        try:
            self._wake_fd_read, self._wake_fd_write = os.pipe()
            logging.debug(
                f"Wake channel for {self} is opened with "
                f"rfd={self._wake_fd_read:d} and wfd={self._wake_fd_write:d}"
            )

            self._poll = select.epoll()
            self._poll.register(
                self._wake_fd_read, select.EPOLLIN | select.EPOLLET
            )

            for fd, event_mask in self._fds:
                self._poll.register(fd, event_mask)

            self.actor_inbox._actor = self
        except Exception:
            self._handle_failure(*sys.exc_info())
            return

        super()._start_actor_loop()

    def _stop(self):
        super()._stop()

        os.close(self._wake_fd_write)
        os.close(self._wake_fd_read)

    def _listen(self, timeout):
        assert (
            self._poll is not None
        ), "Must not request events before poll initialization"

        logging.debug(
            f"Actor {self} is entering poll sleep with timeout = {timeout!r}"
        )
        events = self._poll.poll(timeout)
        logging.debug(f"Actor {self} has been woken with events {events!r}")

        # Don't handle any events if
        # actor has been woken during stopping,
        # so it can quickly finish its lifecycle
        if not self.actor_ref.is_alive():
            return tuple()

        return (
            (fd, event) for (fd, event) in events if fd != self._wake_fd_read
        )

    def _wake(self):
        logging.debug(f"Waking actor {self}")
        os.write(self._wake_fd_write, b"\xFF")

    def _handle_receive(self, message):
        if isinstance(message, ActorError):
            self._handle_failure(*message.exc_info)
            try:
                self.on_failure(*message.exc_info)
            except Exception:
                self._handle_failure(*sys.exc_info())
            return

        if isinstance(message, PollEvent):
            return self.on_poll(message.fd, message.event)

        return super()._handle_receive(message)

    def on_poll(self, fd, event):
        raise NotImplementedError("Use a subclass of PollingActor")

    @classmethod
    def _create_actor_inbox(cls):
        return PollingActorInbox(cls.combine_events)


class PollingActorInbox(queue.Queue):
    def __init__(self, combine_events=False):
        super().__init__()

        self._actor = None
        self._combine_events = combine_events

    def put(self, item, block=True, timeout=None):
        if self._actor is not None:
            self._actor._wake()

        super().put(item, block, timeout)

    def get(self, block=True, timeout=None):
        assert (
            self._actor is not None
        ), "Actor must be set before starting polling"

        while True:
            if not self.empty():
                return super().get(False)

            try:
                # If a non-blocking call is requested simulate
                # it with the minimal timeout of 1 millisecond
                if not block:
                    events = self._actor._listen(1)
                else:
                    # TODO: Since this can be called more than once
                    # we need to properly update timeout if it isn't None
                    events = self._actor._listen(
                        timeout * 1000 if timeout is not None else None
                    )
            except Exception:
                return pykka._envelope.Envelope(
                    ActorError(exc_info=sys.exc_info())
                )

            if self._combine_events:
                events = filter(PollingActorInbox._combine_filter(), events)

            for event in events:
                super().put(pykka._envelope.Envelope(PollEvent(*event)))

            if not block and self.empty():
                raise queue.Empty

    def _combine_filter():
        trigger = False

        def combiner(event):
            nonlocal trigger

            if event[1] & ~(select.EPOLLIN | select.EPOLLOUT | select.EPOLLPRI):
                return True

            if trigger:
                return False

            trigger = True
            return True

        return combiner


class PollEvent(NamedTuple):

    fd: int

    event: int


class ActorError(NamedTuple):
    exc_info: Tuple[Any]
