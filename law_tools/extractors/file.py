class BinaryFile:
    def __init__(self, filename):
        self.fp = open(filename, 'rb')
