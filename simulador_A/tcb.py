from enum import Enum

class State(Enum):
    NEW = 0
    READY = 1
    RUNNING = 2
    SUSPENDED = 3
    TERMINATED = 4


class TCB:

    def __init__(self, id:int, color: str, start:int, duration: int, priority: int):
        self.id = id
        self.color = color
        self.start = start
        self.stop = None
        self.waiting = 0
        self.total_waiting_time = 0
        self.duration = duration
        self.duration_current = 0
        self.priority_init = priority
        self.priority_current = priority
        self.state = State.NEW


    def increment_priority(self):
        self.priority_current += 1


    def increment_duration(self):
        self.duration_current += 1


    def update_state(self, state: State):
        self.state = state


    def finished(self) -> bool:
        return self.duration_current >= self.duration
    

    def print_info(self):
        print(f"ID: {self.id}  ###  Cor: {self.color}  ###  Início: {self.start}  ###  Duration: {self.duration_current}/{self.duration}  ###  Prioridade: {self.priority_init}  ###  State: {self.state}")


    def update(self, time: int):

        if self.state == State.NEW and time >= self.start:
            self.state = State.READY

        elif self.state == State.READY or self.state == State.SUSPENDED:
            self.waiting += 1
            self.total_waiting_time += 1

        elif self.state == State.RUNNING:
            self.waiting = 0
            self.duration_current += 1

            if self.finished():
                self.state = State.TERMINATED

        elif self.state == State.TERMINATED:
            self.stop = time
        