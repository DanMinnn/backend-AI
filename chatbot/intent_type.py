from enum import Enum


class IntentType(Enum):
    CANCEL_ORDER = "cancel_order"
    GENERAL_INQUIRY = "general_inquiry"
    INAPPROPRIATE_CONTENT = "inappropriate_content"
    APP_RELATED = "app_related"