class OriginalArchive:
    def __init__(self, name, url):
        self.name = name
        self.url = url

    def to_dict(self):
        return {
            'name': self.name,
            'url': self.url
        }

    def __str__(self):
        return f'Archive({self.element}, {self.excluded})'
