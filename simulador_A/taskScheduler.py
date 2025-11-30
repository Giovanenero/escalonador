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
    PRIOPEnv = "PRIOPEnv" # preemptivo por prioridade com envelhecimento

    def get_executor(self, scheduler: "TaskScheduler"):
        if self is SchedulerSystemType.FCFS:
            return scheduler._TaskScheduler__execute_fcfs
        elif self is SchedulerSystemType.SRTF:
            return scheduler._TaskScheduler__execute_srtf
        elif self is SchedulerSystemType.PRIOP:
            return scheduler._TaskScheduler__execute_priop
        elif self is SchedulerSystemType.PRIOPEnv:
            return scheduler._TaskScheduler__execute_prioenv
        else:
            raise ValueError(f"Scheduler não suportado: {self}")


class TaskScheduler:
    def __init__(self, type_scheduler: str, quantum: int = None, alpha: int = None):
        self.turnaround_time:float = None
        self.waiting_time:float = None
        self.response_time: float = None
        self.efficiency: float = None
        self.quantum:int = quantum
        self.alpha:int = alpha
        self.remaining_quantum_time: int = 0
        self.type_scheduler = SchedulerSystemType[type_scheduler]


    def task_swap(self, process: Process, task: TCB, mutex: Mutex):
        """Faz a troca de contexto"""
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
        """Execução do algoritmo FCFS"""
        task_running: TCB = process.task_current

        # continua até a que a tarefa saia da seção crítica
        if task_running and mutex.owner and mutex.owner == task_running:
            #if task_running == State.RUNNING:
            self.remaining_quantum_time += 1
            return False

        task_running: TCB = next((task for task in tasks if task.state == State.RUNNING), None)

        # Se não tiver task rodando, tenta encontrar uma tarefa pronta
        if not task_running:
            self.remaining_quantum_time = 1
            task_ready: TCB = next((task for task in tasks if task.state == State.READY), None)
            if not task_ready: # se não tiver tarefa pronta verifica se existe alguma tarefa que está por vir
                task: TCB = next((task for task in tasks if task.state == State.NEW or State.SUSPENDED), None)
                if not task:
                    return True # Não existe mais tarefas para ser processada
                
                return False # aguarda a tarefa ficar pronta
            
            # coloca a tarefa para rodar
            task_ready.state = State.RUNNING
            process.task_current = task_ready
            
            return False

        if self.remaining_quantum_time >= self.quantum:
            self.remaining_quantum_time = 1

            task_running.state = State.READY # coloca a tarefa na fila de pronta

            # pega a próxima tarefa ques está pronta e que não é a mesma que rodou na última execução
            task_ready: TCB = next((task for task in tasks if task.state == State.READY and task != task_running), None)

            # A tarefa continua rodando, pois não tem nenhuma tarefa pronta disponível no momento
            if not task_ready:
                task_running.state = State.RUNNING 
                return False
            
            # troca a tarefa para a próxima até estourar o quantum
            task_ready.state = State.RUNNING
            process.task_current = task_ready

            return False
        
        self.remaining_quantum_time += 1

        return False


    def __execute_srtf(self, process: Process, tasks: list[TCB], mutex:Mutex) -> bool:
        """Execução do algoritmo SRTF"""
        task_running: TCB = process.task_current

        if task_running and task_running.finished():
            task_running.state = State.TERMINATED
            process.task_current = None
            task_running = process.task_current
            self.remaining_quantum_time = 1

        tasks = [task for task in tasks if task.state == State.RUNNING or task.state == State.READY]
        
        if not tasks: # significa que tem tarefa suspensa ou ainda falta carregar na memória
            process.task_current = None
            return False
        
        # se a tarefa atual pertence a seção crítica, deixa ela rodar até sair da seção
        if task_running and mutex.owner and mutex.owner == task_running:
            #if task_running == State.RUNNING:
            self.remaining_quantum_time += 1
            return False

        # faz a troca de tarefa se estourou o quantum
        if task_running and self.remaining_quantum_time >= self.quantum:

            # procura todas as tarefas prontas
            tasks_ready = [task for task in tasks if task.state == State.READY and task != task_running]

            # a tarefa atual continua rodando, pois ainda não existe tarefas prontas
            if not tasks_ready:
                self.remaining_quantum_time += 1
                return False
            
            tasks = tasks_ready
        
        # if task_running.finished():
        #     tasks_ready = [task for task in tasks if task.state == State.READY and task != task_running]

        #     if 


        # procura a tarefa de menor tempo de duração restante
        # se tiver mais de uma tarefa, pega a primeira delas
        task = min(tasks, key=lambda task: task.duration - task.duration_current)

        if task == task_running:
            self.remaining_quantum_time += 1
            return False
        elif task_running:
            task_running.state = State.SUSPENDED
        
        self.task_swap(process, task, mutex)
        self.remaining_quantum_time = 1

        return False
    

    def __execute_priop(self, process: Process, tasks: list[TCB], mutex:Mutex):
        """Execução do algoritmo PRIOP"""
        task_running: TCB = process.task_current

        # Faz a verificação se a tarefa que está rodando ainda não terminou
        if task_running and task_running.finished():
            task_running.state = State.TERMINATED
            process.task_current = None
            task_running = process.task_current
            self.remaining_quantum_time = 1

        tasks = [task for task in tasks if task.state == State.RUNNING or task.state == State.READY]

        if not tasks: 
            process.task_current = None
            return False
        
        task_running: TCB = process.task_current

        # se a tarefa estiver na seção crítica, continua até que ela saia da seção
        if task_running and mutex.owner and mutex.owner == task_running:
            #if task_running == State.RUNNING:
            self.remaining_quantum_time += 1
            return False

        if task_running and self.remaining_quantum_time >= self.quantum:

            # tenta procurar outra tarefa pronta para executar
            tasks_ready = [task for task in process.tasks if task.state == State.READY and task_running != task]
            
            if not tasks_ready:
                # coloca a última tarefa para executar novamente, pois não encontrou nenhuma tarefa pronta
                self.remaining_quantum_time += 1
                return False
            
            task_running.state = State.SUSPENDED
            tasks = tasks_ready


        # se existir outra tarefa pronta e com prioridade maior que a tarefa atual, faz a troca
        task = max(tasks, key=lambda task: task.priority_init)
        if task != task_running:
            self.remaining_quantum_time = 1
            self.task_swap(process, task, mutex)
        else:
            task_running.state = State.RUNNING
            self.remaining_quantum_time += 1

        return False

        
    def __execute_prioenv(self, process: Process, tasks: list[TCB], mutex: Mutex):
        """Executa o algoritmo PRIOEnv"""

        task_running: TCB = process.task_current

        # Faz a verificação se a tarefa que está rodando ainda não terminou
        if task_running and task_running.finished():
            task_running.state = State.TERMINATED
            process.task_current = None
            task_running = process.task_current
            self.remaining_quantum_time = 1

        tasks = [task for task in tasks if task.state == State.RUNNING or task.state == State.READY]

        if not tasks: 
            process.task_current = None
            return False
        
        task_running: TCB = process.task_current

        tasks_ready = []

        # se a tarefa estiver na seção crítica, continua até que ela saia da seção
        if task_running and mutex.owner and mutex.owner == task_running:
            #if task_running == State.RUNNING:
            self.remaining_quantum_time += 1
            return False

        if task_running and self.remaining_quantum_time >= self.quantum:

            # tenta procurar outra tarefa pronta para executar
            tasks_ready = [task for task in process.tasks if task.state == State.READY and task_running != task]
            
            if not tasks_ready:
                # coloca a última tarefa para executar novamente, pois não encontrou nenhuma tarefa pronta
                self.remaining_quantum_time += 1
                return False
            
            task_running.state = State.SUSPENDED
            tasks = tasks_ready


        # se existir outra tarefa pronta e com prioridade maior que a tarefa atual, faz a troca
        task = max(tasks, key=lambda task: task.priority_init)
        if task != task_running:
            self.remaining_quantum_time = 1

            # incrementa a prioridade, pois o escalonador escolheu outra tarefa
        
            tasks_ready = [t for t in process.tasks if t.state == State.READY and task_running != t and t != task]
            for t in tasks_ready:
                    t.priority_current += self.alpha


            self.task_swap(process, task, mutex)

        else:
            task_running.state = State.RUNNING
            self.remaining_quantum_time += 1


        return False



    def execute(self, process: Process, mutex:Mutex) -> bool:
        """Executa o escalonador com o algoritmo definido na construtora"""
        tasks: list[TCB] = process.tasks
        executor = self.type_scheduler.get_executor(self)
        return executor(process, tasks, mutex)


    def update_metrics(self, process: Process):
        """Atualiza métricas do escalonador"""
        tasks: list[TCB] = process.tasks

        lifetime_sum = 0
        waiting_time_sum = 0

        for task in tasks:

            lifetime_sum += task.stop - task.start
            waiting_time_sum += task.total_waiting_time

        total_tasks = len(tasks)

        self.turnaround_time = lifetime_sum / total_tasks
        self.waiting_time = waiting_time_sum / total_tasks

        