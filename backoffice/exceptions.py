class UnsupportedSourceTypeError(Exception):
    def __init__(self, source_type: str):
        super().__init__(f"Unsupported source type: {source_type}")


class InvalidValueError(Exception):
    def __init__(self, source_id: str, value: str):
        super().__init__(f"Invalid value for source ID {source_id}: {value}")
