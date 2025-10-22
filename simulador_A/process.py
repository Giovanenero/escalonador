from tcb import TCB, State

class Process:
    def __init__(self):
        self.tasks: list[TCB] = []
        self.task_current: TCB = None

    def add_task(self, task: TCB):
        self.tasks.append(task)


    def has_task(self) -> bool:
        if not self.tasks: return False
        return any(task.state != State.TERMINATED for task in self.tasks)
    

    def sort_ready(self):
        self.tasks = sorted(self.tasks, key=lambda task: task.start)
