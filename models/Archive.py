class Archive:
    def __init__(self, element, excluded):
        self.element = element
        self.excluded = excluded

    def to_dict(self):
        return {
            'element': self.element,
            'excluded': self.excluded
        }

    def __str__(self):
        return f'Archive({self.element}, {self.excluded})'
