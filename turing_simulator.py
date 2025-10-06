import json
import sys

class Tape:
    """
    Clase para simular la cinta infinita de la MT.
    Usa un diccionario para posiciones (enteros) -> símbolo.
    El blank es '_' por defecto.
    """
    def __init__(self, initial_content="", blank="_"):
        self.content = {}
        self.blank = blank
        self.head = 0
        if initial_content:
            for i, sym in enumerate(initial_content):
                self.content[i] = sym

    def read(self):
        return self.content.get(self.head, self.blank)

    def write(self, sym):
        if sym == self.blank and self.head not in self.content:
            if self.head in self.content:
                del self.content[self.head]
        else:
            self.content[self.head] = sym

    def move(self, direction):
        if direction == 'R':
            self.head += 1
        elif direction == 'L':
            self.head -= 1
        # 'N' No hace nada

    def __str__(self):
        if not self.content:
            return f"...{self.blank}[{self.blank}]..."
        positions = sorted(self.content.keys())
        if not positions:
            return f"...{self.blank}[{self.blank}]..."
        min_pos, max_pos = min(positions), max(positions)
        start = max(min_pos - 5, self.head - 25, -50)
        end = min(max_pos + 5, self.head + 25, 50)
        s = []
        for pos in range(start, end + 1):
            sym = self.content.get(pos, self.blank)
            if pos == self.head:
                s.append(f"[{sym}]")
            else:
                s.append(sym)
        left_ellipsis = "..." if start > min_pos - 5 else ""
        right_ellipsis = "..." if end < max_pos + 5 else ""
        return left_ellipsis + "".join(s) + right_ellipsis


class TransitionFunction:
    """
    Función de transición δ: (estado, símbolo) -> (nuevo_estado, nuevo_símbolo, dirección)
    Almacenada en un diccionario para acceso O(1).
    """
    def __init__(self):
        self.transitions = {}

    def add(self, current_state, read_sym, next_state, write_sym, direction):
        key = (current_state, read_sym)
        self.transitions[key] = (next_state, write_sym, direction)

    def get(self, state, sym):
        return self.transitions.get((state, sym))


class TuringMachine:
    """
    Clase principal para la Máquina de Turing.
    Refleja la definición formal: 7-tupla (Q, Σ, Γ, δ, q0, F, B).
    """
    def __init__(self, states, input_alphabet, tape_alphabet, initial_state, accept_states, blank="_"):
        self.states = states
        self.input_alphabet = input_alphabet
        self.tape_alphabet = tape_alphabet
        self.initial_state = initial_state
        self.accept_states = accept_states
        self.reject_states = {"q_reject"}
        self.blank = blank
        self.transition_function = TransitionFunction()
        self.current_state = None
        self.tape = None

    def add_transition(self, current, read, next_s, write, dir):
        self.transition_function.add(current, read, next_s, write, dir)

    def load_input(self, input_str):
        if any(c not in self.input_alphabet + [self.blank] for c in input_str):
            raise ValueError("Símbolos inválidos en la entrada.")
        self.tape = Tape(input_str, self.blank)
        self.current_state = self.initial_state

    def step(self):
        if self.current_state in self.accept_states:
            return 'accept'
        if self.current_state in self.reject_states:
            return 'reject'

        sym = self.tape.read()
        trans = self.transition_function.get(self.current_state, sym)
        if trans is None:
            return 'reject'

        next_state, write_sym, direction = trans
        self.tape.write(write_sym)
        self.tape.move(direction)
        self.current_state = next_state
        return 'continue'

    def run(self, max_steps=10000, step_by_step=False):
        if not self.tape:
            raise ValueError("Carga una entrada primero con load_input().")
        history = []
        steps = 0
        while steps < max_steps:
            config = self.get_config()
            history.append(config)
            if step_by_step:
                print(f"Paso {steps + 1}: {config}")
                input("Presiona Enter para continuar....")
            result = self.step()
            if result != 'continue':
                final_config = self.get_config()
                history.append(final_config)
                return result, history
            steps += 1
        return 'loop', history

    def get_config(self):
        return {
            'estado': self.current_state,
            'cinta': str(self.tape),
            'cabezal': self.tape.head
        }


def create_on1n_machine():
    """
    Crea una MT estricta para L = {0^n 1^n | n >= 0}.
    - q0: Escanea 0s desde izquierda; al ver Y (fin de 0s), va a q3.
    - q1: Busca 1 después de marcar 0 (salta 0s/X/Y).
    - q2: Regresa izquierda hasta blank inicial.
    - q3: Verifica solo X/Y hasta blank (rechaza 0/1 extras).
    Alfabeto cinta: {0,1,X=0 marcado,Y=1 marcado,_}
    """
    states = ["q0", "q1", "q2", "q3", "q_accept", "q_reject"]
    input_alphabet = ["0", "1"]
    tape_alphabet = ["0", "1", "X", "Y", "_"]
    initial = "q0"
    accept = ["q_accept"]

    tm = TuringMachine(states, input_alphabet, tape_alphabet, initial, accept, "_")

    # q0: escanear desde izquierda para 0 no marcado o fin de fase 0s
    tm.add_transition("q0", "_", "q3", "_", "R")  # Blank inicial: verificar (cadena vacía o fin)
    tm.add_transition("q0", "0", "q1", "X", "R")  # Marcar 0, buscar 1
    tm.add_transition("q0", "1", "q_reject", "1", "N")  # 1 prematuro: rechazar
    tm.add_transition("q0", "X", "q0", "X", "R")  # Saltar 0 marcado
    tm.add_transition("q0", "Y", "q3", "Y", "R")  # CORRECCIÓN CLAVE: Fin de 0s (primer Y), ir a verificación

    # q1: buscar 1 no marcado (salta 0s restantes, X, Y)
    tm.add_transition("q1", "0", "q1", "0", "R")  # Saltar 0s no procesados
    tm.add_transition("q1", "1", "q2", "Y", "L")  # Marcar 1, regresar izquierda
    tm.add_transition("q1", "X", "q1", "X", "R")  # Saltar X
    tm.add_transition("q1", "Y", "q1", "Y", "R")  # Saltar Y (1s ya marcados)
    tm.add_transition("q1", "_", "q_reject", "_", "N")  # Sin 1 correspondiente: rechazar

    # q2: regresar izquierda hasta blank inicial
    tm.add_transition("q2", "_", "q0", "_", "R")  # Llegó izquierda, reiniciar q0
    tm.add_transition("q2", "0", "q2", "0", "L")  # Saltar
    tm.add_transition("q2", "1", "q2", "1", "L")  # Saltar (por completitud)
    tm.add_transition("q2", "X", "q2", "X", "L")  # Saltar
    tm.add_transition("q2", "Y", "q2", "Y", "L")  # Saltar

    # q3: verificar sin símbolos no marcados (solo X/Y permitidos)
    tm.add_transition("q3", "X", "q3", "X", "R")  # Saltar X
    tm.add_transition("q3", "Y", "q3", "Y", "R")  # Saltar Y
    tm.add_transition("q3", "0", "q_reject", "0", "N")  # 0 extra: rechazar
    tm.add_transition("q3", "1", "q_reject", "1", "N")  # 1 extra: rechazar
    tm.add_transition("q3", "_", "q_accept", "_", "N")  # Todo marcado correctamente: aceptar

    return tm


def main():
    tm = create_on1n_machine()
    print("Simulador de MT para {0^n 1^n} estricta.")
    input_str = input("Ingresa la cadena de entrada (ej. 0101): ").strip()
    tm.load_input(input_str)

    mode = input("Modo: 'auto' o 'step' (paso a paso)? ").strip().lower()
    step_by_step = mode == 'step'

    result, history = tm.run(step_by_step=step_by_step, max_steps=10000)
    print(f"\nResultado: {result.upper()}")
    if result == 'loop':
        print("Se detectó un posible bucle (límite de pasos alcanzado).")
    print(f"Pasos totales: {len(history) - 1}")
    print("Configuración final:")
    print(f"Estado: {history[-1]['estado']}")
    print(f"Cinta: {history[-1]['cinta']}")
    print(f"Cabezal: {history[-1]['cabezal']}")


# Pruebas unitarias básicas
if __name__ == "__main__":
    print("=== PRUEBAS ===")
    tm = create_on1n_machine()

    tests = [
        ("", "accept"),       # n=0
        ("01", "accept"),     # n=1
        ("0011", "accept"),   # n=2
        ("001", "reject"),    # Más 0s que 1s
        ("1100", "reject"),   # Orden invertido (1s antes)
        ("0101", "reject")    # Intercalado (igual conteo pero orden malo)
    ]

    for inp, expected in tests:
        tm.load_input(inp)
        result, _ = tm.run(step_by_step=False, max_steps=1000)
        status = "OK" if result == expected else "FAIL"
        print(f"Entrada '{inp}': {result} (esperado: {expected}) - {status}")

    print("\nModo interactivo.")
    main()  # Descomenta para CLIK interactiva