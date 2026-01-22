#!/usr/bin/env python3
"""
Sistema completo - BANTAM EMPIEZA INMEDIATAMENTE DESPUÉS DE VISION BLUE
"""

import simpy


class Config:
    # Robot1
    ROBOT1_IDLE_TO_CAPTURE = 5.14
    ROBOT1_VISION = 1.8
    ROBOT1_PICK_AND_PLACE = 13.56
    ROBOT1_TO_HOME = 7.0
    ROBOT1_HOME_TO_IDLE = 2.0

    # Conveyor1
    CONVEYOR1_TRANSPORT_TIME = 13.5

    # Conveyor2
    CONVEYOR2_TRANSPORT_TIME = 12.5

    # xArm1
    XARM1_IDLE_TO_PICK_C1S2 = 8.5
    XARM1_C1S2_TO_C2S1 = 13.5
    XARM1_C2S1_TO_IDLE = 7.0
    XARM1_IDLE_TO_PICK_LASER = 7.0
    XARM1_LASER_TO_C2S1 = 15.0
    XARM1_C1S2_TO_LASER = 15.0

    # Laser
    LASER_HEATING = 30.0
    LASER_PROCESSING = 23.5

    # Robot2
    ROBOT2_IDLE_TO_CAPTURE = 3.8
    ROBOT2_VISION = 2.0
    ROBOT2_CAPTURE_TO_PICK = 8.3
    ROBOT2_PICK_TO_RED_STACK = 13.0
    ROBOT2_PICK_TO_GREEN_STACK = 13.5
    ROBOT2_STACK_TO_IDLE = 7.0
    ROBOT2_PICK_TO_IBS = 13.0
    ROBOT2_IBS_TO_IDLE = 5.5
    ROBOT2_PICK_TO_BANTAM = 17.5
    ROBOT2_BANTAM_TO_IDLE = 6.5
    ROBOT2_IDLE_TO_BANTAM_PICK = 8.0
    ROBOT2_BANTAM_TO_BLUE_STACK = 18.0
    ROBOT2_BLUE_STACK_TO_IDLE = 5.32
    ROBOT2_IDLE_TO_IBS_PICK = 10.0
    ROBOT2_IBS_TO_BANTAM_PLACE = 15.0
    ROBOT2_BANTAM_PLACE_TO_IDLE = 6.0

    # Bantam
    BANTAM_HEATING = 10.0
    BANTAM_PROCESSING = 25.0


class System:
    def __init__(self, env):
        self.env = env
        self.initial_stack = ["BLUE", "RED", "GREEN", "RED", "GREEN", "BLUE",
                              "GREEN", "BLUE", "RED", "GREEN", "GREEN"]

        self.c1s1_occupied = False
        self.c1s2_occupied = False
        self.c1s2_piece = None
        self.c1s2_color = None
        self.conveyor1_running = True
        self.pieces_on_conveyor1 = []

        self.c2s1_occupied = False
        self.c2s2_occupied = False
        self.c2s2_piece = None
        self.c2s2_color = None
        self.conveyor2_running = True
        self.pieces_on_conveyor2 = []

        self.robot1_state = "IDLE"
        self.robot2_state = "IDLE"
        self.xarm1_state = "IDLE"
        self.piece_counter = 0

        self.laser_state = "IDLE"
        self.laser_piece = None

        self.bantam_state = "IDLE"
        self.bantam_piece = None

        self.ibs_pieces = []

        self.final_red_stack = []
        self.final_green_stack = []
        self.final_blue_stack = []

    def log(self, msg):
        print(f"[{self.env.now:7.2f}s] {msg}")


def robot1_process(env, system):
    system.log("🤖 Robot1 → IDLE")
    while len(system.initial_stack) > 0:
        if system.robot1_state == "IDLE" and not system.c1s1_occupied:
            system.piece_counter += 1
            color = system.initial_stack.pop(0)
            piece_name = f"PIECE_{system.piece_counter}"
            system.log(f"📦 Robot1 ciclo: {piece_name} ({color})")
            system.robot1_state = "WORKING"

            yield env.timeout(Config.ROBOT1_IDLE_TO_CAPTURE)
            yield env.timeout(Config.ROBOT1_VISION)
            system.log(f"🎨 Vision1 → {color}")
            yield env.timeout(Config.ROBOT1_PICK_AND_PLACE)

            system.log(f"📦 {piece_name} → C1S1")
            system.c1s1_occupied = True
            system.log("📤 C1S1 → OCCUPIED")
            system.pieces_on_conveyor1.append(
                {'name': piece_name, 'color': color})

            yield env.timeout(Config.ROBOT1_TO_HOME)
            yield env.timeout(Config.ROBOT1_HOME_TO_IDLE)
            system.robot1_state = "IDLE"
            system.log("✅ Robot1 → IDLE")
        else:
            yield env.timeout(0.1)
    system.log("🏁 Robot1 finalizado")


def conveyor1_process(env, system):
    while True:
        if system.conveyor1_running and len(system.pieces_on_conveyor1) > 0:
            piece_data = system.pieces_on_conveyor1.pop(0)
            system.log(f"🔄 Conveyor1 transportando {piece_data['name']}")
            system.c1s1_occupied = False
            system.log("📤 C1S1 → FREE")
            yield env.timeout(Config.CONVEYOR1_TRANSPORT_TIME)
            system.log(f"📦 {piece_data['name']} → C1S2")
            system.c1s2_piece = piece_data['name']
            system.c1s2_color = piece_data['color']
            system.c1s2_occupied = True
            system.log("📤 C1S2 → OCCUPIED")
            system.conveyor1_running = False
            system.log("⏸️  Conveyor1 → PARADO")
        else:
            yield env.timeout(0.1)


def conveyor1_control(env, system):
    while True:
        if not system.c1s2_occupied and not system.conveyor1_running:
            system.conveyor1_running = True
            system.log("▶️  Conveyor1 → CORRIENDO")
        yield env.timeout(0.1)


def conveyor2_process(env, system):
    while True:
        if system.conveyor2_running and len(system.pieces_on_conveyor2) > 0:
            piece_data = system.pieces_on_conveyor2.pop(0)
            system.log(f"🔄 Conveyor2 transportando {piece_data['name']}")
            system.c2s1_occupied = False
            system.log("📤 C2S1 → FREE")
            yield env.timeout(Config.CONVEYOR2_TRANSPORT_TIME)
            system.log(f"📦 {piece_data['name']} → C2S2")
            system.c2s2_piece = piece_data['name']
            system.c2s2_color = piece_data['color']
            system.c2s2_occupied = True
            system.log("📤 C2S2 → OCCUPIED")
            system.conveyor2_running = False
            system.log("⏸️  Conveyor2 → PARADO")
        else:
            yield env.timeout(0.1)


def conveyor2_control(env, system):
    while True:
        if not system.c2s2_occupied and not system.conveyor2_running:
            system.conveyor2_running = True
            system.log("▶️  Conveyor2 → CORRIENDO")
        yield env.timeout(0.1)


def laser_process(env, system, piece_name):
    system.laser_state = "WORKING"
    system.log(f"🔥 Laser → WORKING ({piece_name})")
    yield env.timeout(Config.LASER_HEATING)
    system.log(f"🔥 Laser → Procesando...")
    yield env.timeout(Config.LASER_PROCESSING)
    system.laser_state = "FINISHED"
    system.log(f"✅ Laser → FINISHED ({piece_name})")


def bantam_process(env, system, piece_name):
    """Bantam - Empieza inmediatamente después de vision"""
    system.bantam_state = "WORKING"
    system.log(f"🔧 Bantam → WORKING ({piece_name})")

    # 10 segundos calentamiento
    yield env.timeout(Config.BANTAM_HEATING)
    system.log(f"🔧 Bantam → Calentado, iniciando procesado...")

    # 35 segundos procesado
    yield env.timeout(Config.BANTAM_PROCESSING)

    system.bantam_state = "FINISHED"
    system.log(f"✅ Bantam → FINISHED ({piece_name})")


def xarm1_process(env, system):
    system.log("🦾 xArm1 → IDLE")
    while True:
        if system.xarm1_state == "IDLE" and system.laser_state == "FINISHED":
            if system.c2s1_occupied:
                yield env.timeout(0.1)
                continue
            piece_name = system.laser_piece
            system.log(f"🔴 xArm1 P1: Vaciar laser ({piece_name})")
            system.xarm1_state = "WORKING"
            yield env.timeout(Config.XARM1_IDLE_TO_PICK_LASER)
            system.laser_piece = None
            system.laser_state = "IDLE"
            system.log("🔥 Laser → IDLE")
            yield env.timeout(Config.XARM1_LASER_TO_C2S1)
            system.c2s1_occupied = True
            system.pieces_on_conveyor2.append(
                {'name': piece_name, 'color': 'RED'})
            yield env.timeout(Config.XARM1_C2S1_TO_IDLE)
            system.xarm1_state = "IDLE"
            system.log("✅ xArm1 → IDLE")
        elif system.xarm1_state == "IDLE" and system.c1s2_occupied:
            piece_name = system.c1s2_piece
            color = system.c1s2_color
            if color == "RED":
                if system.laser_state == "WORKING":
                    yield env.timeout(0.1)
                    continue
                if system.laser_state == "FINISHED":
                    continue
                system.log(f"🔴 xArm1 P2: {piece_name} → Laser")
                system.xarm1_state = "WORKING"
                env.process(laser_process(env, system, piece_name))
                yield env.timeout(Config.XARM1_IDLE_TO_PICK_C1S2)
                system.c1s2_occupied = False
                system.c1s2_piece = None
                system.c1s2_color = None
                system.log("📤 C1S2 → FREE")
                yield env.timeout(Config.XARM1_C1S2_TO_LASER)
                system.laser_piece = piece_name
                yield env.timeout(Config.XARM1_C2S1_TO_IDLE)
                system.xarm1_state = "IDLE"
                system.log("✅ xArm1 → IDLE")
            else:
                if system.c2s1_occupied:
                    yield env.timeout(0.1)
                    continue
                system.log(
                    f"{'🟢' if color == 'GREEN' else '🔵'} xArm1 P2: {piece_name} → C2S1")
                system.xarm1_state = "WORKING"
                yield env.timeout(Config.XARM1_IDLE_TO_PICK_C1S2)
                system.c1s2_occupied = False
                system.c1s2_piece = None
                system.c1s2_color = None
                system.log("📤 C1S2 → FREE")
                yield env.timeout(Config.XARM1_C1S2_TO_C2S1)
                system.c2s1_occupied = True
                system.pieces_on_conveyor2.append(
                    {'name': piece_name, 'color': color})
                yield env.timeout(Config.XARM1_C2S1_TO_IDLE)
                system.xarm1_state = "IDLE"
                system.log("✅ xArm1 → IDLE")
        else:
            yield env.timeout(0.1)


def robot2_process(env, system):
    system.log("🤖 Robot2 → IDLE")
    while True:
        # PRIORIDAD 1: Procesar C2S2
        if system.robot2_state == "IDLE" and system.c2s2_occupied:
            piece_name = system.c2s2_piece
            color = system.c2s2_color
            system.log(f"📦 Robot2 P1: Procesar C2S2 - {piece_name} ({color})")
            system.robot2_state = "WORKING"

            yield env.timeout(Config.ROBOT2_IDLE_TO_CAPTURE)
            yield env.timeout(Config.ROBOT2_VISION)
            system.log(f"🎨 Vision2 → {color}")

            # ⚡ SI ES AZUL Y BANTAM IDLE → BANTAM EMPIEZA AQUÍ
            bantam_will_process_this_piece = False
            if color == "BLUE" and system.bantam_state == "IDLE":
                env.process(bantam_process(env, system, piece_name))
                bantam_will_process_this_piece = True

            yield env.timeout(Config.ROBOT2_CAPTURE_TO_PICK)
            system.c2s2_occupied = False
            system.c2s2_piece = None
            system.c2s2_color = None
            system.log("📤 C2S2 → FREE")

            if color == "BLUE":
                if bantam_will_process_this_piece:
                    # Bantam ya empezó con esta pieza, Robot2 solo la lleva
                    system.log(f"🔵 Robot2 → BANTAM")
                    yield env.timeout(Config.ROBOT2_PICK_TO_BANTAM)
                    system.bantam_piece = piece_name  # ✅ ASIGNAR PIEZA
                    yield env.timeout(Config.ROBOT2_BANTAM_TO_IDLE)
                elif system.bantam_state == "WORKING" or system.bantam_state == "FINISHED":
                    # Bantam ocupado con otra pieza → IBS
                    system.log(
                        f"🔵 Robot2 → IBS (Bantam {system.bantam_state})")
                    yield env.timeout(Config.ROBOT2_PICK_TO_IBS)
                    system.ibs_pieces.append(piece_name)
                    system.log(
                        f"📦 {piece_name} → IBS (Buffer: {len(system.ibs_pieces)})")
                    yield env.timeout(Config.ROBOT2_IBS_TO_IDLE)
                system.robot2_state = "IDLE"
                system.log("✅ Robot2 → IDLE")
            elif color == "RED":
                yield env.timeout(Config.ROBOT2_PICK_TO_RED_STACK)
                system.final_red_stack.append(piece_name)
                yield env.timeout(Config.ROBOT2_STACK_TO_IDLE)
                system.robot2_state = "IDLE"
                system.log("✅ Robot2 → IDLE")
            else:  # GREEN
                yield env.timeout(Config.ROBOT2_PICK_TO_GREEN_STACK)
                system.final_green_stack.append(piece_name)
                yield env.timeout(Config.ROBOT2_STACK_TO_IDLE)
                system.robot2_state = "IDLE"
                system.log("✅ Robot2 → IDLE")

        # PRIORIDAD 2: Vaciar Bantam
        elif system.robot2_state == "IDLE" and system.bantam_state == "FINISHED":
            piece_name = system.bantam_piece
            system.log(f"🔧 Robot2 P2: Vaciar Bantam ({piece_name})")
            system.robot2_state = "WORKING"
            yield env.timeout(Config.ROBOT2_IDLE_TO_BANTAM_PICK)
            system.bantam_piece = None
            system.bantam_state = "IDLE"
            system.log("🔧 Bantam → IDLE")
            yield env.timeout(Config.ROBOT2_BANTAM_TO_BLUE_STACK)
            system.final_blue_stack.append(piece_name)
            yield env.timeout(Config.ROBOT2_BLUE_STACK_TO_IDLE)
            system.robot2_state = "IDLE"
            system.log("✅ Robot2 → IDLE")

        # PRIORIDAD 3: IBS → Bantam
        elif system.robot2_state == "IDLE" and system.bantam_state == "IDLE" and len(system.ibs_pieces) > 0:
            piece_name = system.ibs_pieces.pop(0)
            system.log(f"🔵 Robot2 P3: IBS → Bantam ({piece_name})")
            system.robot2_state = "WORKING"

            # ⚡ BANTAM EMPIEZA AQUÍ (para piezas de IBS)
            env.process(bantam_process(env, system, piece_name))

            yield env.timeout(Config.ROBOT2_IDLE_TO_IBS_PICK)
            yield env.timeout(Config.ROBOT2_IBS_TO_BANTAM_PLACE)
            system.bantam_piece = piece_name
            yield env.timeout(Config.ROBOT2_BANTAM_PLACE_TO_IDLE)
            system.robot2_state = "IDLE"
            system.log("✅ Robot2 → IDLE")
        else:
            yield env.timeout(0.1)


def run_simulation():
    env = simpy.Environment()
    system = System(env)

    print("=" * 70)
    print("🚀 SISTEMA COMPLETO - BANTAM EMPIEZA INMEDIATAMENTE")
    print("=" * 70)
    print(f"Piezas: {system.initial_stack}")
    print("=" * 70)

    env.process(robot1_process(env, system))
    env.process(conveyor1_process(env, system))
    env.process(conveyor1_control(env, system))
    env.process(conveyor2_process(env, system))
    env.process(conveyor2_control(env, system))
    env.process(xarm1_process(env, system))
    env.process(robot2_process(env, system))

    env.run(until=1000)

    print("\n" + "=" * 70)
    print("📊 ESTADO FINAL")
    print("=" * 70)
    print(f"Tiempo: {env.now:.2f}s")
    print(f"🔴 RED: {len(system.final_red_stack)} - {system.final_red_stack}")
    print(
        f"🟢 GREEN: {len(system.final_green_stack)} - {system.final_green_stack}")
    print(
        f"🔵 BLUE: {len(system.final_blue_stack)} - {system.final_blue_stack}")
    print(f"📦 IBS: {len(system.ibs_pieces)} piezas")
    print("=" * 70)


if __name__ == "__main__":
    run_simulation()
