from enum import Enum
from mutex import Mutex

class State(Enum):
    NEW = 0
    READY = 1
    RUNNING = 2
    SUSPENDED = 3
    TERMINATED = 4


class TCB:

    def __init__(self, id:int, color: str, start:int, duration: int, priority: int, events: list[dict]):
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
        self.events = events


    def increment_priority(self):
        self.priority_current += 1


    def increment_duration(self):
        self.duration_current += 1


    def finished(self) -> bool:
        return self.duration_current >= self.duration
    

    def print_info(self):
        print(f"ID: {self.id}  ###  Cor: {self.color}  ###  Início: {self.start}  ###  Duration: {self.duration_current}/{self.duration}  ###  Prioridade: {self.priority_init}  ###  State: {self.state}")


    def update_events(self, mutex: Mutex):
        # não processa se a tarefa não estiver ativa para processar eventos
        # (chame update_events apenas quando estiver RUNNING ou SUSPENDED conforme seu fluxo)
        active_events = []

        # 1) remover eventos já concluídos (iterar sobre cópia)
        for event in self.events[:]:
            if event['duration_current'] >= event['duration']:
                self.events.remove(event)

        # 2) coletar eventos que já começaram (relativo ao progresso da tarefa)
        for event in self.events:
            if self.duration_current >= event['start']:
                active_events.append(event)

        has_interrupt = next((True for event in active_events if 'IO' in event['type']), False)

        if (not active_events or not has_interrupt) and self.state == State.SUSPENDED:
            if mutex.owner and mutex.owner.id == self.id:
                self.state = State.RUNNING
            else:
                self.state = State.READY
            return

        # 3) processar eventos ativos (um por vez pode ser adequado)
        for event in active_events:
            event_type = event['type']

            # I/O: suspende e avança contagem
            if 'IO' in event_type:
                self.state = State.SUSPENDED
                event['duration_current'] += 1
                # quando terminar, na próxima iteração o evento será removido pela etapa 1

            # Mutex Lock
            elif 'ML' in event_type:
                # se livre, adquiri
                if not mutex.locked or (mutex.owner and mutex.owner.id == self.id):
                    mutex.locked = True
                    mutex.owner = self   # salva o TCB
                    print(f"[t] {self.id} adquiriu o mutex")
                    # remover o evento ML (já consumido)

                    if event in self.events:
                        self.events.remove(event)
                else:
                    # mutex ocupado: tarefa bloqueia e entra na fila de espera (se ainda não estiver)
                    if self not in mutex.waiting_queue:
                        mutex.waiting_queue.append(self)
                    self.state = State.SUSPENDED
                    # NÃO remove o evento ML — opcionalmente você pode manter o ML até ser despertado
                    # e então removê-lo quando reentrar (ou remover já e manter uma flag)

            # Mutex Unlock
            elif 'MU' in event_type:
                # só o dono pode liberar
                if mutex.owner.id == self.id:

                    mutex.locked = False
                    mutex.owner = None
                    print(f"[t] {self.id} liberou o mutex")
                    # acorda o próximo (se houver)

                    print(len(mutex.waiting_queue))
                    if mutex.waiting_queue:
                        next_tcb = mutex.waiting_queue.pop(0)
                        next_tcb.state = State.READY

                        print(f"[t] {next_tcb.id} acordou (mutex disponível)")
                    # remove o evento MU
                    if event in self.events:
                        self.events.remove(event)

                    ml_mu = [event for event in self.events if 'ML' in event['type'] or 'MU' in event['type']]
                    if next((True for event in ml_mu if 'MU' in event['type']), False):
                        mutex.owner = self
                        mutex.locked = True
                        print(f"[t] {self.id} readquiriu o mutex automaticamente")
                        return

                else:
                    # se não for dono, ignorar MU (ou logar erro)
                    if event in self.events:
                        self.events.remove(event)


    def update_state(self, time: int, mutex:Mutex):

        if self.state == State.NEW and time >= self.start:
            self.state = State.READY

        elif self.state == State.READY:
            self.waiting += 1
            self.total_waiting_time += 1

        elif self.state == State.SUSPENDED:

            if self.finished():
                self.state = State.TERMINATED
                self.stop = time
            else:
                self.waiting += 1
                self.total_waiting_time += 1
                self.update_events(mutex)

        elif self.state == State.RUNNING:
            self.waiting = 0
            self.duration_current += 1
            self.update_events(mutex)

            if self.finished():
                self.state = State.TERMINATED
                self.stop = time

        #elif self.state == State.TERMINATED:
        #    self.stop = time
        