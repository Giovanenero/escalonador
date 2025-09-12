from task import Task, State

class Process:
    def __init__(self):
        self.tasks: list[Task] = []
        self.task_current: Task = None

    def add_task(self, task: Task):
        self.tasks.append(task)


    def has_task(self) -> bool:
        return any(task.state != State.TERMINATED for task in self.tasks)
    

    def sort_ready(self):
        self.tasks = sorted(self.tasks, key=lambda task: task.start)