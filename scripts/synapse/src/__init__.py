class AzResource:
    """
    Base object class that represents an azure resource
    """

    def __init__(self, name: str, properties: dict):
        self.name = name
        self.properties = properties


class AzDependency:

    def __init__(self, name, type):
        self.name = name
        self.type = type

    def formatARM(self):
        t = (self.type[0].lower() + self.type[1:]).replace("Reference",
                                                           "") + "s"
        return f"/{t}/{self.name}"

    def __eq__(self, other):
        return (self.name == other.name) and \
               (self.type == other.type)

    def __neq__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return self.formatARM()
