from tcb import TCB, State
from process import Process
from taskScheduler import TaskScheduler
import os, matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from mutex import Mutex
import random

DEFAULT_ALGORITHM = "FCFS"
DEFAULT_QUANTUM = 2

DEFAULT_TASKS = """
t01;#1f77b4;0;5;2;IO:2-1;IO:3-2\n
t02;#ff7f0e;0;4;3;IO:3-1\n
t03;#2ca02c;3;5;5;ML:1;MU:3\n
t04;#d62728;5;6;9;ML:1;IO:2-1;MU:3\n
t05;#9467bd;7;4;6;ML:1;IO:2-1;MU:3
"""

RANDOM_INIT = 0
RANDOM_END = 10

def plot_timeline(timeline_dict: dict, tasks: list[TCB], ax_graph, ax_table, algoritmo: str, quantum: int, save=True):
    """Atualiza a interface gráfica do usuário"""
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

    # --- Legenda com o algoritmo e quantum ---
    ax_graph.text(
        0.5, 1.05, 
        f"Algoritmo: {algoritmo} | Quantum: {QUANTUM} | Running: {quantum}", 
        ha='center', va='bottom', transform=ax_graph.transAxes,
        fontsize=10, fontweight='bold'
    )

    # --- Tabela ---
    ax_table.axis('off')
    table_data = [
        [
            task.id, 
            task.color, 
            task.start, 
            f"{task.duration_current}/{task.duration}", 
            task.priority_init,
            ", ".join([f'{event["start"]}/{event["duration"]}/{event["duration_current"]}' for event in task.events if 'IO' in event['type']]), 
            ", ".join([f'{event["type"]}:{event["start"]}' for event in task.events if event['type'] in ['ML', 'MU']]),
            "1" if task == MUTEX.owner else "0",
            task.state.name
        ] 
        for task in tasks
    ]
    col_labels = ["ID", "Cor", "Início", "Duração", "Prioridade", "IO", "ML/MU", "Lock", "Estado"]

    cell_colors = []
    for task in tasks:
        row_colors = ['white'] * len(col_labels)
        row_colors[1] = task.color
        cell_colors.append(row_colors)

    ax_table.table(
        cellText=table_data, 
        colLabels=col_labels, 
        cellLoc='center', 
        colLoc='center', 
        loc='center', 
        cellColours=cell_colors
    )

    plt.draw()
    plt.pause(0.01)
    if save:
        plt.savefig('./plt.png', dpi=300, bbox_inches="tight")


# def print_gantt(timeline_dict: dict, time: int):

#     print("\nTempo:  " + "  ".join(f'{index:02}' for index in range(time)))

#     keys: int = sorted(list(timeline_dict.keys()))

#     for key in keys:
#         print(f"{key}      " + "   ".join(status for status in timeline_dict[key][:-1]))


def initialize() -> tuple[int, int, list[TCB]]:
    """Obtém o algoritmo, o valor do quantum e inicializa a lista de tarefas definida no arquivo .txt"""

    # pega apenas o primeiro arquivo .txt do diretório atual
    file = next((file for file in os.listdir('./') if file.endswith('.txt') and file not in ['default_file.txt', 'requirements.txt']), None)
   
    # se não existir o arquivo, o sistema escolhe o tipo de algoritmo, quantum e as tarefas
    if not file:

        opcao = input('Arquivo do .txt do usuário não encontrado. Utilizar o arquivo padrão para popular a lista de tarefas(s/n):\n\nResposta: ')
        opcao = opcao.lower()

        if opcao in ['s', 'sim', 'yes', 'y']:
            file = os.path.join(os.getcwd(), 'default_file.txt')
            # faz a leitura do arquivo
            with open(file, 'r', encoding="utf-8") as file:
                lines = file.readlines()

        else:
            algorithm = input('Deseja escolher qual algoritmo?\n\n1 - FCFS\n2 - SRTF\n3 - PRIOP\n\nResposta: ')
            if '1' in algorithm:
                algorithm = 'FCFS'
            elif '2' in algorithm:
                algorithm = 'SRTF'
            elif '3' in algorithm:
                algorithm = 'PRIOP'
            else:
                print('Não existe este algoritmo')
                exit(1)
            
            quantum = input('Defina um valor de quantum: ')

            try:
                quantum = int(quantum)
            except:
                print('Erro ao tentar definir o valor de quantum')
                exit(1)

            tasks_count = input('Defina a quantidade de tarefas: ')
            try:
                tasks_count = int(tasks_count)
            except:
                print('Erro ao tentar definir a quantidade de tarefas')
                exit(1)

            lines = [f"{algorithm};{quantum}"]
            lines += [
                f"t{index + 1:02d};" +                # ID com 2 dígitos
                f"#{random.randint(0, 0xFFFFFF):06x};" +  # Cor aleatória
                f"{random.randint(RANDOM_INIT, RANDOM_END)};" +  # Ingresso
                f"{random.randint(RANDOM_INIT, RANDOM_END)};" +  # Duração
                f"{random.randint(RANDOM_INIT, RANDOM_END)}"     # Prioridade
                for index in range(0, tasks_count)
            ]
    else:

        # faz a leitura do arquivo
        with open(file, 'r', encoding="utf-8") as file:
            lines = file.readlines()
    
    # lê a primeira linha com o tipo do algoritmo e o valor do quantum
    items = lines[0].strip().split(';')
    algorithm = items[0] if items[0] else DEFAULT_ALGORITHM
    quantum = int(items[1]) if items[1] else DEFAULT_QUANTUM

    tasks: list[TCB] = []

    # inicializa as tarefas e adiciona dentro do processo
    try:

        for task in lines[1:]:

            if not task and not task.strip():
                continue

            items: list[str] = [item.strip() for item in task.strip().split(';')]

            events: list[dict] = []
            # =====================================================================
            # A lista de eventos faz parte do simulador B
            # =====================================================================
            # for item in items[5:]:
            #     if not item:
            #         continue
            #     event_type, time_event = item.split(':')
            #     if 'IO' in event_type:
            #         start_s, dur_s = time_event.split('-')
            #         events.append({
            #             'type': event_type,
            #             'start': int(start_s),
            #             'duration': int(dur_s),
            #             'duration_current': 0
            #         })
            #     else:  # ML ou MU
            #         events.append({
            #             'type': event_type,
            #             'start': int(time_event),
            #             'duration': 1,               # opcional — para marcar ocorrência
            #             'duration_current': 0
            #         })

            try:
                if len(items) == 3:
                    # significa que o usuário não adicionou uma cor
                    if '#' not in items[1]:
                        tcb: TCB = TCB(
                            items[0],       # pid
                            "#{:06x}".format(random.randint(0, 0xFFFFFF)),       # color
                            int(items[1]),  # ingresso
                            int(items[2]),  # duração
                            int(items[3]),  # prioridade
                            events
                        )
                else:            
                    tcb: TCB = TCB(
                        items[0],       # pid
                        items[1],       # color
                        int(items[2]),  # ingresso
                        int(items[3]),  # duração
                        int(items[4]),  # prioridade
                        events
                    )

            except Exception as e:
                print(f'ERRO | def initialize | {e}')
                tcb: TCB = TCB(
                    f"t{len(tasks) + 1:02d}",                       # pid
                    "#{:06x}".format(random.randint(0, 0xFFFFFF)),  # color
                    random.randint(RANDOM_INIT, RANDOM_END),        # ingresso
                    random.randint(RANDOM_INIT, RANDOM_END),        # duração
                    random.randint(RANDOM_INIT, RANDOM_END),        # prioridade
                    events
                )


            tasks.append(tcb)

    except Exception as e:
        print(f'ERRO | def initialize | {e}')
        return

    return algorithm, quantum, tasks
    

def save_timeline(timeline_dict: dict, tasks: list[TCB]) -> dict:
    """Salva os estados das tarefas"""
    for task in tasks:
        timeline_dict[task.id].append(
            ' ' if task.state == State.READY else 
            task.color if task.state == State.RUNNING else 
            ' ' if task.state == State.SUSPENDED else
            't' if task.start == State.TERMINATED else 'n'
        )

    return timeline_dict


def run():
    global MUTEX, QUANTUM

    algorithm, QUANTUM, tasks = initialize()

    process = Process() # cria o process
    for task in tasks:
        process.add_task(task) # adiciona a tarefa no processo

    process.sort_ready() # ordena as tarefas por ordem de ingresso

    task_scheduler = TaskScheduler(algorithm, QUANTUM)

    time = 0
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

    MUTEX = Mutex()

    while True: 

        #print(f'================================================= TIME: {time} =================================================\n')

        tasks: list[TCB] = process.tasks

        # inicializa o estado das tarefas
        for task in tasks:
            task.update_state(time, MUTEX)

        # se não tiver tarefa no process, finaliza o processo
        if not process.has_task():
            break

        # chama o escalonador para decidir qual tarefa deve rodar
        task_scheduler.execute(process, MUTEX)

        timeline_dict = save_timeline(timeline_dict, tasks)

        if 'a' in opcao:
            plot_timeline(timeline_dict, tasks, ax_graph, ax_table, algoritmo=algorithm, quantum=task_scheduler.remaining_quantum_time)
            #sleep(0.5)
            input('pressione ENTER para continuar')


            #print(f"ID: {task.id}  ###  Cor: {task.color}  ###  Início: {task.start}  ###  Duration: {task.duration_current}/{task.duration}  ###  Prioridade: {task.priority_init}  ###  State: {task.state}")

        time += 1


    process.task_current.stop = time
    task_scheduler.update_metrics(process)

    print(f'\nTt = {task_scheduler.turnaround_time} s')
    print(f'Tw = {task_scheduler.waiting_time} s')


    plot_timeline(timeline_dict, tasks, ax_graph, ax_table, algoritmo=algorithm, quantum=task_scheduler.remaining_quantum_time)

    input('pressione ENTER para continuar')

if __name__ == '__main__':
    run()
