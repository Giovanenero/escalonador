from tcb import TCB, State
from process import Process
from taskScheduler import TaskScheduler
import os, matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from time import sleep


def plot_timeline(timeline_dict: dict, tasks: list[TCB], ax_graph, ax_table, save=True):
    ax_graph.clear()
    ax_table.clear()

    # --- Gráfico ---
    for i, (task_id, timeline) in enumerate(timeline_dict.items(), start=1):
        for t, state in enumerate(timeline):
            if state == ' ':          # READY
                color = "lightgray"
            elif state == 'n':        # NOT_STARTED / PRONTA
                color = "white"
            else:                     # RUNNING
                color = state

            ax_graph.broken_barh([(t, 1)], (i - 0.4, 0.8), facecolors=color)

    ax_graph.set_xlabel("Tempo")
    ax_graph.set_ylabel("Tarefas")
    ax_graph.set_yticks(range(1, len(timeline_dict) + 1))
    ax_graph.set_yticklabels([f"P{tid}" for tid in timeline_dict.keys()])
    ax_graph.set_xticks(range(len(next(iter(timeline_dict.values())))))

    # --- Tabela ---
    ax_table.axis('off')
    table_data = [[task.id, task.color, task.start, f"{task.duration_current}/{task.duration}", task.priority_init, task.state.name] for task in tasks]
    col_labels = ["ID", "Cor", "Início", "Duração", "Prioridade", "Estado"]

    cell_colors = []
    for task in tasks:
        # Preenche a cor apenas na coluna 1 (índice 1), o resto fica branco
        row_colors = ['white'] * len(col_labels)
        row_colors[1] = task.color
        cell_colors.append(row_colors)

    ax_table.table(cellText=table_data, colLabels=col_labels, cellLoc='center', colLoc='center', loc='center', cellColours=cell_colors)


    #ax_table.table(cellText=table_data, colLabels=col_labels, cellLoc='center', colLoc='center', loc='center')


    plt.draw()
    plt.pause(0.01)
    if save:
        plt.savefig('./plt.png', dpi=300, bbox_inches="tight")


def print_gantt(timeline_dict: dict, time: int):

    print("\nTempo:  " + "  ".join(f'{index:02}' for index in range(time)))

    keys: int = sorted(list(timeline_dict.keys()))

    for key in keys:
        print(f"{key}      " + "   ".join(status for status in timeline_dict[key][:-1]))


def initialize() -> tuple[int, int, list[TCB]]:

    file = next((file for file in os.listdir('./') if file.endswith('.txt')), None)

    with open(file, 'r', encoding="utf-8") as file:
        lines = file.readlines()

    items = lines[0].strip().split(';')
    algorithm: str = items[0]
    quantum: int = int(items[1])

    tasks: list[TCB] = []

    for task in lines[1:]:

        items: list[str] = [item for item in task.strip().split(';')]

        events: list[dict] = [ 
            {
                'type': event_type, 
                'start': int(time_event.split('-')[0]), 
                'duration': int(time_event.split('-')[1]),
                'duration_current': 0
            }
            for item in items[5:] if item != ''
            for event_type, time_event in [item.split(':')]
        ]
        
        
        tcb: TCB = TCB(
            items[0],       # pid
            items[1],       # color
            int(items[2]),  # ingresso
            int(items[3]),  # duração
            int(items[4]),  # prioridade
            events
        )
        tasks.append(tcb)

    return algorithm, quantum, tasks
    

def save_timeline(timeline_dict: dict, tasks: list[TCB]) -> dict:
    for task in tasks:
        timeline_dict[task.id].append(
            ' ' if task.state == State.READY else 
            task.color if task.state == State.RUNNING else 
            ' ' if task.state == State.SUSPENDED else
            't' if task.start == State.TERMINATED else 'n'
        )

    return timeline_dict


def run():

    algorithm, quantum, tasks = initialize()

    process = Process() # cria o process
    for task in tasks:
        process.add_task(task) # adiciona a tarefa no processo

    process.sort_ready() # ordena as tarefas por ordem de ingresso

    task_scheduler = TaskScheduler(algorithm, quantum)

    time = 0
    terminated = False
    timeline_dict = {task.id: [] for task in tasks}

    opcao = input('Execução das tarefas:\n\nA: Passo-a-passo\nB: Completa\n\nResposta: ')
    opcao = opcao.lower()

    if not ('a' in opcao or 'b' in opcao):
        print('Resposta incorreta')
        exit(1)


    plt.ion()
    fig = plt.figure(figsize=(14, 6))
    gs = GridSpec(2, 1, height_ratios=[3, 1], figure=fig)
    ax_graph = fig.add_subplot(gs[0])
    ax_table = fig.add_subplot(gs[1])

    while True: 

        #print(f'================================================= TIME: {time} =================================================\n')

        tasks: list[TCB] = process.tasks

        # atualizar a tarefa e o estado de todas as tarefas com base no tempo atual
        for task in tasks:
            task.update_state(time)
            task.update_events(time)
            #print(f"ID: {task.id}  ###  Cor: {task.color}  ###  Início: {task.start}  ###  Duration: {task.duration_current}/{task.duration}  ###  Prioridade: {task.priority_init}  ###  State: {task.state}")

        # chama o escalonador para decidir qual tarefa deve rodar
        terminated = task_scheduler.execute(process)

        # atualiza a tarefa
        # process.task_update(time)

        timeline_dict = save_timeline(timeline_dict, tasks)

        if 'a' in opcao:
            plot_timeline(timeline_dict, tasks, ax_graph, ax_table)
            #sleep(0.5)
            input('pressione qualquer tecla')

        # se não tiver tarefa no process, finaliza o processo
        terminated = not process.has_task()
        if terminated:
            break

        time += 1


    process.task_current.stop = time
    task_scheduler.update_metrics(process)

    print(f'\nTt = {task_scheduler.turnaround_time} s')
    print(f'Tw = {task_scheduler.waiting_time} s')


    if 'b' in opcao:
        plot_timeline(timeline_dict, tasks, ax_graph, ax_table)

    input('precione qualquer tecla...')

if __name__ == '__main__':
    run()



# 2
# 11 0010 == 50

#50

#40

#01000


# 50

# 1_0_0000 = 32
# 0_1_0000 = 16

# 1_0_0000 se >=

# 0_1_0000 se >= 16
