class Mutex:
    def __init__(self):
        self.locked = False
        self.owner = None
        self.waiting_queue = []