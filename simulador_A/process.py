from tcb import TCB, State

class Process:
    def __init__(self):
        self.tasks: list[TCB] = []
        self.task_current: TCB = None

    def add_task(self, task: TCB):
        self.tasks.append(task)


    def has_task(self) -> bool:
        return any(task.state != State.TERMINATED for task in self.tasks)
    

    def sort_ready(self):
        self.tasks = sorted(self.tasks, key=lambda task: task.start)


    def task_update(self, time: int):

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