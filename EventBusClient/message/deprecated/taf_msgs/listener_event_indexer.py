"""The listener event indexer module.

This module implements a compact indexer specialized for the synchronization
across multiple TAF instances. The idea is to pack all possible states into
one 64-bit integer (hence 'compact') that is guaranteed to be numerically
comparable.
"""

from numpy import uint16, uint32, uint64, iinfo

EventIndex = uint64

SPECIAL_CODE_PREFIX = EventIndex(iinfo(uint32).max) << EventIndex(32)


class ListenerEventIndexer:  # pylint: disable=R0904:too-many-public-methods
    """The listener event indexer class."""

    def __init__(self, index: EventIndex = 0):
        """Initialize."""
        self.__cycle_state = uint32(0)
        self.__suite_state = uint16(0)
        self.__test_state = uint16(0)
        if index != 0:
            self.decode(index)

    @classmethod
    def is_special_code(cls, code: EventIndex) -> bool:
        """Check if a number is code for special purpose."""
        return SPECIAL_CODE_PREFIX == (SPECIAL_CODE_PREFIX & code)

    @classmethod
    def is_recovery_code(cls, code: EventIndex) -> bool:
        """Check if a number is code for recovery mode."""
        return cls.is_special_code(code) and \
            (1 == (code >> 16) & 0x00000000000000FF)

    @classmethod
    def recovery_code(cls, scope: int) -> EventIndex:
        """Return special code for recovery mode."""
        return (
            (SPECIAL_CODE_PREFIX) |
            (EventIndex(1) << 16) |
            (EventIndex(scope))
        )

    @classmethod
    def get_recovery_scope(cls, code: EventIndex) -> int:
        """Extract recovery scope from code."""
        return code & 0x00000000000000FF

    def encode(self) -> EventIndex:
        """Return the combined index."""
        return (
            (EventIndex(self.__cycle_state) << 32) |
            (EventIndex(self.__suite_state) << 16) |
            (EventIndex(self.__test_state))
        )

    def decode(self, index: EventIndex):
        """Decompose the combined index."""
        idx = EventIndex(index)
        self.__test_state = uint16(idx & 0x00000000000000FF)
        self.__suite_state = uint16((idx >> 16) & 0x00000000000000FF)
        self.__cycle_state = uint32(idx >> 32)

    def suite_setup_intro(self) -> bool:
        """Check if suite setup started."""
        return (3 < self.__suite_state) and \
            (0 == (self.__suite_state & 0x0003))

    def suite_setup_outro(self) -> bool:
        """Check if suite setup completed."""
        return (3 < self.__suite_state) and \
            (1 == (self.__suite_state & 0x0003))

    def suite_teardown_intro(self) -> bool:
        """Check if suite teardown started."""
        return (3 < self.__suite_state) and \
            (2 == (self.__suite_state & 0x0003))

    def suite_teardown_outro(self) -> bool:
        """Check if suite teardown completed."""
        return (3 < self.__suite_state) and \
            (3 == (self.__suite_state & 0x0003))

    def test_setup_intro(self) -> bool:
        """Check if test setup started."""
        return (3 < self.__test_state) and \
            (0 == (self.__test_state & 0x0003))

    def test_setup_outro(self) -> bool:
        """Check if test setup completed."""
        return (3 < self.__test_state) and \
            (1 == (self.__test_state & 0x0003))

    def test_teardown_intro(self) -> bool:
        """Check if test teardown started."""
        return (3 < self.__test_state) and \
            (2 == (self.__test_state & 0x0003))

    def test_teardown_outro(self) -> bool:
        """Check if test teardown completed."""
        return (3 < self.__test_state) and \
            (3 == (self.__test_state & 0x0003))

    @property
    def cycle_index(self) -> uint32:
        """Getter for cycle index."""
        return self.__cycle_state

    @property
    def suite_state(self) -> uint16:
        """Getter for suite state."""
        return self.__suite_state

    @property
    def suite_index(self) -> uint16:
        """Getter for suite index."""
        return self.__suite_state >> 2

    @property
    def test_state(self) -> uint16:
        """Getter for test state."""
        return self.__test_state

    @property
    def test_index(self) -> uint16:
        """Getter for test index."""
        return self.__test_state >> 2

    def reset_cycle_state(self):
        """Reset cycle state."""
        self.__cycle_state = uint32(0)

    def reset_suite_state(self):
        """Reset suite state."""
        self.__suite_state = uint16(0)

    def reset_test_state(self):
        """Reset test state."""
        self.__test_state = uint16(0)

    def inc_cycle_state(self):
        """Move up the cycle index to next state."""
        # reset test index at new cycle
        self.__test_state = uint16(0)
        # reset suite index at new cycle
        self.__suite_state = uint16(0)
        # increment by 1 to mark the next state
        self.__cycle_state += 1

    def inc_suite_state(self):
        """Move up the suite index to next state."""
        if not self.__cycle_state:
            # cycle has not started
            return

        if not self.__suite_state:
            # init the suite index
            self.__suite_state = 4
            return

        if 3 == (self.__suite_state & 0x0003):
            # reset test index at END_SUITE_CLOSE
            self.__test_state = uint16(0)

        # increment by 1 to mark the next state
        self.__suite_state += 1

    def inc_test_state(self):
        """Move up the test index to next state."""
        if not self.__suite_state:
            # parent suite hasn't started
            return

        if not self.__test_state:
            # init the test index
            self.__test_state = 4
            return

        # increment by 1 to mark the next state
        self.__test_state += 1
