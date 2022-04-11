class _AzureResource:
    """
    Base object class that represents an azure resource
    """

    def __init__(self, name: str, properties: dict):
        self.name = name
        self.properties = properties
