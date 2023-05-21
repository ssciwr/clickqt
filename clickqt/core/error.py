from enum import IntEnum

class ClickQtError(IntEnum):
    NO_ERROR = 0
    CONFIRMATION_INPUT_NOT_EQUAL_ERROR = 1

    def __str__(self):
        match(self.value):
            case ClickQtError.NO_ERROR: return ""
            case ClickQtError.CONFIRMATION_INPUT_NOT_EQUAL_ERROR: return "Confirmation input is not equal"

        return "Unknown"