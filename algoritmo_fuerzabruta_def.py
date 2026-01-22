#!/usr/bin/env python3
"""
Optimizador de Secuencia - FUERZA BRUTA
Nueva lógica: BANTAM EMPIEZA INMEDIATAMENTE DESPUÉS DE VISION
"""

import simpy
from itertools import permutations
from typing import List
import time

# ============================================================================
# CONFIGURACIÓN
# ============================================================================


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

# ============================================================================
# SISTEMA CON NUEVA LÓGICA (sin prints)
# ============================================================================


class System:
    def __init__(self, env, initial_stack):
        self.env = env
        self.initial_stack = list(initial_stack)

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

        self.total_pieces = len(initial_stack)
        self.completion_time = 0


def robot1_process(env, system):
    while len(system.initial_stack) > 0:
        if system.robot1_state == "IDLE" and not system.c1s1_occupied:
            system.piece_counter += 1
            color = system.initial_stack.pop(0)
            piece_name = f"P{system.piece_counter}"
            system.robot1_state = "WORKING"

            yield env.timeout(Config.ROBOT1_IDLE_TO_CAPTURE)
            yield env.timeout(Config.ROBOT1_VISION)
            yield env.timeout(Config.ROBOT1_PICK_AND_PLACE)

            system.c1s1_occupied = True
            system.pieces_on_conveyor1.append(
                {'name': piece_name, 'color': color})

            yield env.timeout(Config.ROBOT1_TO_HOME)
            yield env.timeout(Config.ROBOT1_HOME_TO_IDLE)
            system.robot1_state = "IDLE"
        else:
            yield env.timeout(0.1)


def conveyor1_process(env, system):
    while True:
        if system.conveyor1_running and len(system.pieces_on_conveyor1) > 0:
            piece_data = system.pieces_on_conveyor1.pop(0)
            system.c1s1_occupied = False
            yield env.timeout(Config.CONVEYOR1_TRANSPORT_TIME)
            system.c1s2_piece = piece_data['name']
            system.c1s2_color = piece_data['color']
            system.c1s2_occupied = True
            system.conveyor1_running = False
        else:
            yield env.timeout(0.1)


def conveyor1_control(env, system):
    while True:
        if not system.c1s2_occupied and not system.conveyor1_running:
            system.conveyor1_running = True
        yield env.timeout(0.1)


def conveyor2_process(env, system):
    while True:
        if system.conveyor2_running and len(system.pieces_on_conveyor2) > 0:
            piece_data = system.pieces_on_conveyor2.pop(0)
            system.c2s1_occupied = False
            yield env.timeout(Config.CONVEYOR2_TRANSPORT_TIME)
            system.c2s2_piece = piece_data['name']
            system.c2s2_color = piece_data['color']
            system.c2s2_occupied = True
            system.conveyor2_running = False
        else:
            yield env.timeout(0.1)


def conveyor2_control(env, system):
    while True:
        if not system.c2s2_occupied and not system.conveyor2_running:
            system.conveyor2_running = True
        yield env.timeout(0.1)


def laser_process(env, system, piece_name):
    system.laser_state = "WORKING"
    yield env.timeout(Config.LASER_HEATING)
    yield env.timeout(Config.LASER_PROCESSING)
    system.laser_state = "FINISHED"


def bantam_process(env, system, piece_name):
    """⚡ NUEVA LÓGICA: Empieza inmediatamente después de vision"""
    system.bantam_state = "WORKING"
    yield env.timeout(Config.BANTAM_HEATING)
    yield env.timeout(Config.BANTAM_PROCESSING)
    system.bantam_state = "FINISHED"


def xarm1_process(env, system):
    while True:
        if system.xarm1_state == "IDLE" and system.laser_state == "FINISHED":
            if system.c2s1_occupied:
                yield env.timeout(0.1)
                continue
            piece_name = system.laser_piece
            system.xarm1_state = "WORKING"
            yield env.timeout(Config.XARM1_IDLE_TO_PICK_LASER)
            system.laser_piece = None
            system.laser_state = "IDLE"
            yield env.timeout(Config.XARM1_LASER_TO_C2S1)
            system.c2s1_occupied = True
            system.pieces_on_conveyor2.append(
                {'name': piece_name, 'color': 'RED'})
            yield env.timeout(Config.XARM1_C2S1_TO_IDLE)
            system.xarm1_state = "IDLE"
        elif system.xarm1_state == "IDLE" and system.c1s2_occupied:
            piece_name = system.c1s2_piece
            color = system.c1s2_color
            if color == "RED":
                if system.laser_state == "WORKING":
                    yield env.timeout(0.1)
                    continue
                if system.laser_state == "FINISHED":
                    continue
                system.xarm1_state = "WORKING"
                env.process(laser_process(env, system, piece_name))
                yield env.timeout(Config.XARM1_IDLE_TO_PICK_C1S2)
                system.c1s2_occupied = False
                system.c1s2_piece = None
                system.c1s2_color = None
                yield env.timeout(Config.XARM1_C1S2_TO_LASER)
                system.laser_piece = piece_name
                yield env.timeout(Config.XARM1_C2S1_TO_IDLE)
                system.xarm1_state = "IDLE"
            else:
                if system.c2s1_occupied:
                    yield env.timeout(0.1)
                    continue
                system.xarm1_state = "WORKING"
                yield env.timeout(Config.XARM1_IDLE_TO_PICK_C1S2)
                system.c1s2_occupied = False
                system.c1s2_piece = None
                system.c1s2_color = None
                yield env.timeout(Config.XARM1_C1S2_TO_C2S1)
                system.c2s1_occupied = True
                system.pieces_on_conveyor2.append(
                    {'name': piece_name, 'color': color})
                yield env.timeout(Config.XARM1_C2S1_TO_IDLE)
                system.xarm1_state = "IDLE"
        else:
            yield env.timeout(0.1)


def robot2_process(env, system):
    while True:
        # PRIORIDAD 1: Procesar C2S2
        if system.robot2_state == "IDLE" and system.c2s2_occupied:
            piece_name = system.c2s2_piece
            color = system.c2s2_color
            system.robot2_state = "WORKING"

            yield env.timeout(Config.ROBOT2_IDLE_TO_CAPTURE)
            yield env.timeout(Config.ROBOT2_VISION)

            # ⚡ NUEVA LÓGICA: SI ES AZUL Y BANTAM IDLE → BANTAM EMPIEZA AQUÍ
            bantam_will_process_this_piece = False
            if color == "BLUE" and system.bantam_state == "IDLE":
                env.process(bantam_process(env, system, piece_name))
                bantam_will_process_this_piece = True

            yield env.timeout(Config.ROBOT2_CAPTURE_TO_PICK)
            system.c2s2_occupied = False
            system.c2s2_piece = None
            system.c2s2_color = None

            if color == "BLUE":
                if bantam_will_process_this_piece:
                    yield env.timeout(Config.ROBOT2_PICK_TO_BANTAM)
                    system.bantam_piece = piece_name
                    yield env.timeout(Config.ROBOT2_BANTAM_TO_IDLE)
                elif system.bantam_state in ["WORKING", "FINISHED"]:
                    yield env.timeout(Config.ROBOT2_PICK_TO_IBS)
                    system.ibs_pieces.append(piece_name)
                    yield env.timeout(Config.ROBOT2_IBS_TO_IDLE)
                system.robot2_state = "IDLE"
            elif color == "RED":
                yield env.timeout(Config.ROBOT2_PICK_TO_RED_STACK)
                system.final_red_stack.append(piece_name)
                yield env.timeout(Config.ROBOT2_STACK_TO_IDLE)
                system.robot2_state = "IDLE"
            else:  # GREEN
                yield env.timeout(Config.ROBOT2_PICK_TO_GREEN_STACK)
                system.final_green_stack.append(piece_name)
                yield env.timeout(Config.ROBOT2_STACK_TO_IDLE)
                system.robot2_state = "IDLE"

        # PRIORIDAD 2: Vaciar Bantam
        elif system.robot2_state == "IDLE" and system.bantam_state == "FINISHED":
            piece_name = system.bantam_piece
            system.robot2_state = "WORKING"
            yield env.timeout(Config.ROBOT2_IDLE_TO_BANTAM_PICK)
            system.bantam_piece = None
            system.bantam_state = "IDLE"
            yield env.timeout(Config.ROBOT2_BANTAM_TO_BLUE_STACK)
            system.final_blue_stack.append(piece_name)
            yield env.timeout(Config.ROBOT2_BLUE_STACK_TO_IDLE)
            system.robot2_state = "IDLE"

        # PRIORIDAD 3: IBS → Bantam
        elif system.robot2_state == "IDLE" and system.bantam_state == "IDLE" and len(system.ibs_pieces) > 0:
            piece_name = system.ibs_pieces.pop(0)
            system.robot2_state = "WORKING"

            # ⚡ NUEVA LÓGICA: BANTAM EMPIEZA AQUÍ (para piezas de IBS)
            env.process(bantam_process(env, system, piece_name))

            yield env.timeout(Config.ROBOT2_IDLE_TO_IBS_PICK)
            yield env.timeout(Config.ROBOT2_IBS_TO_BANTAM_PLACE)
            system.bantam_piece = piece_name
            yield env.timeout(Config.ROBOT2_BANTAM_PLACE_TO_IDLE)
            system.robot2_state = "IDLE"
        else:
            yield env.timeout(0.1)


def completion_monitor(env, system):
    while True:
        total = len(system.final_red_stack) + \
            len(system.final_green_stack) + \
            len(system.final_blue_stack)
        if total == system.total_pieces:
            system.completion_time = env.now
            break
        yield env.timeout(0.5)


def simulate(sequence: List[str]) -> float:
    """Simula una secuencia con la NUEVA LÓGICA y retorna tiempo total"""
    env = simpy.Environment()
    system = System(env, sequence)

    env.process(robot1_process(env, system))
    env.process(conveyor1_process(env, system))
    env.process(conveyor1_control(env, system))
    env.process(conveyor2_process(env, system))
    env.process(conveyor2_control(env, system))
    env.process(xarm1_process(env, system))
    env.process(robot2_process(env, system))
    env.process(completion_monitor(env, system))

    env.run(until=2000)

    total = len(system.final_red_stack) + \
        len(system.final_green_stack) + \
        len(system.final_blue_stack)
    if total == system.total_pieces:
        return system.completion_time
    else:
        return 9999.0

# ============================================================================
# FUERZA BRUTA
# ============================================================================


def brute_force_optimize():
    """Prueba TODAS las permutaciones únicas con NUEVA LÓGICA"""

    # 8 piezas: 3R, 3G, 2B (ajusta según necesites)
    pieces = ["GREEN", "RED", "BLUE", "RED",  "BLUE", "BLUE"]
    print("=" * 70)
    print("🔍 OPTIMIZACIÓN POR FUERZA BRUTA - NUEVA LÓGICA BANTAM")
    print("=" * 70)
    print(f"Problema: 3 RED + 3 GREEN + 2 BLUE = 8 piezas")
    print(f"Nueva lógica: Bantam empieza inmediatamente después de visión")
    print("=" * 70)

    # Generar permutaciones únicas
    unique_sequences = set(permutations(pieces))
    total = len(unique_sequences)

    print(f"\n🔄 Evaluando {total} secuencias...\n")

    results = []
    start_time = time.time()

    for i, seq in enumerate(unique_sequences, 1):
        seq_list = list(seq)
        completion_time = simulate(seq_list)
        results.append({
            'sequence': seq_list,
            'time': completion_time
        })

        if i % 100 == 0 or i == total:
            elapsed = time.time() - start_time
            eta = (elapsed / i) * (total - i)
            print(f"Progreso: {i}/{total} ({i*100/total:.1f}%) | "
                  f"Tiempo: {elapsed:.1f}s | ETA: {eta:.1f}s")

    # Ordenar por tiempo
    results.sort(key=lambda x: x['time'])

    print("\n" + "=" * 70)
    print("🏆 RESULTADOS")
    print("=" * 70)

    # Top 10
    print("\n📊 TOP 10 MEJORES SECUENCIAS:")
    for i, result in enumerate(results[:10], 1):
        seq_str = ' '.join([c[0] for c in result['sequence']])
        print(f"{i:2d}. {result['time']:6.2f}s | {seq_str}")

    # Peores 5
    print("\n📊 PEORES 5 SECUENCIAS:")
    for i, result in enumerate(results[-5:], 1):
        seq_str = ' '.join([c[0] for c in result['sequence']])
        print(f"{i:2d}. {result['time']:6.2f}s | {seq_str}")

    # Estadísticas
    times = [r['time'] for r in results if r['time'] < 9999]
    best = results[0]
    worst = results[-1]
    avg = sum(times) / len(times)

    print("\n" + "=" * 70)
    print("📈 ESTADÍSTICAS")
    print("=" * 70)
    print(f"Mejor tiempo:  {best['time']:.2f}s")
    print(f"Peor tiempo:   {worst['time']:.2f}s")
    print(f"Promedio:      {avg:.2f}s")
    print(
        f"Diferencia:    {worst['time'] - best['time']:.2f}s ({(worst['time']/best['time']-1)*100:.1f}%)")

    print("\n🏆 SECUENCIA ÓPTIMA:")
    print(f"Tiempo: {best['time']:.2f}s")
    print(f"Secuencia completa: {best['sequence']}")
    print(f"Patrón: {' '.join([c[0] for c in best['sequence']])}")

    return results


if __name__ == "__main__":
    results = brute_force_optimize()
