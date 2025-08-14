from EventBusClient.message.base_message import BaseMessage

class DictMessage(BaseMessage):
    """
    DictMessage: A message that can be initialized from a dictionary.
    """

    def __init__(self, data: dict = None):
        super().__init__()
        self.data = data or {}

    @classmethod
    def from_data(cls, data: dict):
        return cls(data)

    def get_value(self):
        return self.data