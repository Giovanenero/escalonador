from task import Task
from process import Process
from taskScheduler import TaskScheduler, SchedulerSystemType

def run():

    task_a = Task(1, 4, 3, 4)
    task_b = Task(2, 2, 7, 2)
    task_c = Task(3, 3, 4, 2)
    task_d = Task(4, 1, 1, 2)


    process = Process()
    process.add_task(task_a)
    process.add_task(task_b)
    process.add_task(task_c)
    process.add_task(task_d)

    process.sort_ready() # ordena as tarefas por ordem de ingresso

    task_scheduler = TaskScheduler(SchedulerSystemType.PRIOP)

    time = 0
    terminated = False

    while True: 

        for task in process.tasks:
            task.update(time)
            task.print_info() 

        terminated = task_scheduler.execute(process)

        if terminated:
            break

        time += 1
        print(f'======================= TIME: {time} =======================\n')



    process.task_current.stop = time
    task_scheduler.update_metrics(process)

    print(f'Tt = {task_scheduler.turnaround_time}')
    print(f'Tw = {task_scheduler.waiting_time}')


if __name__ == '__main__':
    run()