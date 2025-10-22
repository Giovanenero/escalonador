from enum import Enum
from process import Process
from tcb import TCB, State
from mutex import Mutex

# A classe Escalonador de Tarefas(Task Scheduler) é quem decide
# a ordem de execução das tarefas

# Tipos de Tarefas: orientadas a processamento (CPU-bound tasks)
class SchedulerSystemType(Enum):
    FCFS = "FCFS"   # cooperativo
    SRTF = "SRTF"   # preemptivo
    PRIOP = "PRIOP" # preemptivo por prioridade

    def get_executor(self, scheduler: "TaskScheduler"):
        if self is SchedulerSystemType.FCFS:
            return scheduler._TaskScheduler__execute_fcfs
        elif self is SchedulerSystemType.SRTF:
            return scheduler._TaskScheduler__execute_strf
        elif self is SchedulerSystemType.PRIOP:
            return scheduler._TaskScheduler__execute_priop
        else:
            raise ValueError(f"Scheduler não suportado: {self}")


class TaskScheduler:
    def __init__(self, type_scheduler: str, quantum: int = None):
        self.turnaround_time:float = None
        self.waiting_time:float = None
        self.response_time: float = None
        self.efficiency: float = None
        self.__quantum:int = quantum
        self.__remaining_quantum_time: int = 0
        self.type_scheduler = SchedulerSystemType[type_scheduler.upper()]

        #self.__index_cooperative = 0 # se o escalonador for cooperativo, este atributo se faz relevante para o gerenciamento das tarefas


    # def task_swap(self, process: Process, task: TCB, mutex:Mutex):

    #     if process.task_current != task:

    #         if process.task_current and \
    #         process.task_current.state != State.TERMINATED and \
    #         process.task_current.state != State.SUSPENDED:
                
    #             process.task_current.state = State.READY

    #         if process.task_current and mutex.owner == process.task_current.id:
    #             task.state = State.SUSPENDED

    #         else:

    #             task.state = State.RUNNING
    #             process.task_current = task

    def task_swap(self, process: Process, task: TCB, mutex: Mutex):
        # se já está em execução, nada a fazer
        if process.task_current == task:
            return

        # se o mutex está travado por outro TCB, a tarefa candidata não pode rodar
        if mutex.locked and mutex.owner is not None and mutex.owner != task:
            # não podemos colocar 'task' para RUNNING — ela fica READY
            return

        # coloca a tarefa atualmente em CPU de volta para READY (se aplicável)
        if process.task_current and process.task_current.state not in (State.TERMINATED, State.SUSPENDED):
            process.task_current.state = State.READY

        # troca: coloca a candidata para RUNNING
        task.state = State.RUNNING
        process.task_current = task


    def __execute_fcfs(self, process: Process, tasks: list[TCB], mutex:Mutex) -> bool:
        
        task_running: TCB = next((task for task in tasks if task.state == State.RUNNING), None)

        if task_running:
            return False

        task_ready: TCB = next((task for task in tasks if task.state == State.READY), None)
        
        if task_ready:
            task_ready.state = State.RUNNING
            process.task_current = task_ready
            return False


        return True


        # while self.__index_cooperative < len(tasks):
        #     task_running, index_running = next(((task, index) for index, task in enumerate(tasks) if task.state == State.RUNNING), (None, -1))

        #     if task_running:


        #     if task_running is None:
        #         task_ready, index_ready = next(((task, index) for index, task in enumerate(tasks) if task.state == State.READY), (None, -1))




        #     task: TCB = next(task for task in tasks if task.state)
        #     task: TCB = tasks[self.__index_cooperative]

        #     if task.state == State.TERMINATED:
        #         self.__index_cooperative += 1

        #     elif task.state == State.READY:
        #         task.state = State.RUNNING
        #         process.task_current = task
        #         break

        #     else: break
        
        #return self.__index_cooperative >= len(tasks) # siginica que totas as tarefa foram terminadas


    def __execute_strf(self, process: Process, tasks: list[TCB], mutex:Mutex) -> bool:

        tasks = [task for task in tasks if task.state == State.RUNNING or task.state == State.READY]
        
        if not tasks: # significa que tem tarefa suspensa ou ainda falta carregar na memória
            process.task_current = None
            return False
        
        # procura a tarefa de menor tempo de duração restante
        # se tiver mais de uma tarefa, pega a primeira delas
        task = min(tasks, key=lambda task: task.duration - task.duration_current)
        self.task_swap(process, task, mutex)

        return False
    

    def __execute_priop(self, process: Process, tasks: list[TCB], mutex:Mutex):

        tasks = [task for task in tasks if task.state == State.RUNNING or task.state == State.READY]
        
        if not tasks: 
            process.task_current = None
            return False
        
        task = max(tasks, key=lambda task: task.priority_init)
        self.task_swap(process, task, mutex)

        return False

        
    def execute(self, process: Process, mutex:Mutex) -> bool:
        tasks: list[TCB] = process.tasks
        executor = self.type_scheduler.get_executor(self)
        return executor(process, tasks, mutex)


    def update_metrics(self, process: Process):
        tasks: list[TCB] = process.tasks

        lifetime_sum = 0
        waiting_time_sum = 0

        for task in tasks:

            lifetime_sum += task.stop - task.start
            waiting_time_sum += task.total_waiting_time

        total_tasks = len(tasks)

        self.turnaround_time = lifetime_sum / total_tasks
        self.waiting_time = waiting_time_sum / total_tasks

        