from enum import StrEnum


class NextAction(StrEnum):
    RESEARCHER = "researcher"
    ANALYST = "analyst"
    FINISH = "finish"