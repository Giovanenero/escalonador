from tcb import TCB, State
from process import Process
from taskScheduler import TaskScheduler, SchedulerSystemType
import os


def print_gantt(timeline_dict: dict, time: int):

    print("\nTempo:  " + "  ".join(f'{index}' for index in range(time)))

    keys: int = sorted(list(timeline_dict.keys()))

    for key in keys:
        print(f"P{key}       " + "  ".join(status for status in timeline_dict[key][:-1]))



def initialize() -> tuple[int, int, list[TCB]]:

    file = next((file for file in os.listdir('./') if file.endswith('.txt')), None)

    with open(file, 'r', encoding="utf-8") as file:
        lines = file.readlines()

    items = lines[0].strip().split(';')
    algorithm: int = int(items[0])
    quantum: int = int(items[1])

    tasks: list[TCB] = []

    for task in lines[1:]:
        items: list[int] = [item for item in task.strip().split(';')]
        tcb: TCB = TCB(
            int(items[0]),  # pid
            items[1],       # color
            int(items[2]),  # ingresso
            int(items[3]),  # duração
            int(items[4])   # prioridade
        )
        tasks.append(tcb)

    return algorithm, quantum, tasks
    

def save_timeline(timeline_dict: dict, tasks: list[TCB]) -> dict:
    for task in tasks:
        timeline_dict[task.id].append(
            '_' if task.state == State.READY else 
            task.color if task.state == State.RUNNING else ' '
        )

    return timeline_dict


def run():

    algorithm, quantum, tasks = initialize()

    process = Process() # cria o process
    for task in tasks:
        process.add_task(task) # adiciona a tarefa no processo

    process.sort_ready() # ordena as tarefas por ordem de ingresso

    task_scheduler = TaskScheduler(SchedulerSystemType(algorithm), quantum)

    time = 0
    terminated = False
    timeline_dict = {task.id: [] for task in tasks}

    opcao = input('Execução das tarefas:\n\nA: Passo-a-passo\nB: Completa\n\nResposta: ')
    opcao = opcao.lower()

    if not ('a' in opcao or 'b' in opcao):
        print('Resposta incorreta')
        exit(1)


    while True: 

        print(f'================================================= TIME: {time} =================================================\n')

        tasks: list[TCB] = process.tasks

        # atualizar a tarefa e o estado de todas as tarefas com base no tempo atual
        for task in tasks:
            task.update(time)
            print(f"ID: {task.id}  ###  Cor: {task.color}  ###  Início: {task.start}  ###  Duration: {task.duration_current}/{task.duration}  ###  Prioridade: {task.priority_init}  ###  State: {task.state}")
            #task.print_info()

        # chama o escalonador para decidir qual tarefa deve rodar
        terminated = task_scheduler.execute(process)

        # atualiza a tarefa
        # process.task_update(time)

        timeline_dict = save_timeline(timeline_dict, tasks)
        print_gantt(timeline_dict, time + 1)

        # se não tiver tarefa no process, finaliza o processo
        terminated = not process.has_task()
        if terminated:
            break

        time += 1

        if 'a' in opcao:
            input('\nPressione qualquer tecla...')

        print()



    process.task_current.stop = time
    task_scheduler.update_metrics(process)

    print(f'\nTt = {task_scheduler.turnaround_time}')
    print(f'Tw = {task_scheduler.waiting_time}')


if __name__ == '__main__':
    run()