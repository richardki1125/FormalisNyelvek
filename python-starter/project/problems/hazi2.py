import argparse
from collections import deque
from pathlib import Path
import sys
from project.problem import Problem


class AutomatonDeterminizationProblem(Problem):

    def initialize_parser(self, parser: argparse.ArgumentParser):
        try:
            parser.add_argument(
                "--det",
                action="store_true",
                help="Kapcsoló a determinizálás elvégzéséhez",
            )
        except argparse.ArgumentError:
            pass

    def is_chosen_problem(self, args) -> bool:
        return getattr(args, "det", False) or getattr(args, "problem", "") == "2"

    def run(self, args):
        input_source = getattr(args, "input", None)
        output_target = getattr(args, "output", None)
        self.process_file(input_source, output_target)

    def process_file(self, input_path, output_path):
        valid_states, alphabet, start_state, final_states, transitions = (
            self.load_nfa(input_path)
        )

        dfa_states, dfa_finals, dfa_transitions = self.determinize(
            valid_states, alphabet, start_state, final_states, transitions
        )

        self.write_output(
            output_path,
            dfa_states,
            alphabet,
            "s0",
            dfa_finals,
            dfa_transitions,
        )

    def load_nfa(self, source):
        if source is None or source == "-":
            lines = [line.strip() for line in sys.stdin if line.strip()]
        elif isinstance(source, (str, Path)):
            path = Path(source)
            if not path.exists():
                raise FileNotFoundError(f"A fájl nem található: {source}")
            with open(path, "r", encoding="utf-8") as f:
                lines = [line.strip() for line in f if line.strip()]
        else:
            lines = [line.strip() for line in source if line.strip()]

        if len(lines) < 4:
            raise ValueError(
                "A bemeneti fájl nem tartalmazza a szükséges 4 soros fejlécet!"
            )

        valid_states = lines[0].split()
        valid_states_set = set(valid_states)
        alphabet = lines[1].split()
        start_state = lines[2].strip()
        final_states = set(lines[3].split())

        if start_state not in valid_states_set:
            raise ValueError(
                f"A kezdőállapot ('{start_state}') nem érvényes állapot!"
            )

        for fs in final_states:
            if fs not in valid_states_set:
                raise ValueError(
                    f"A végállapot ('{fs}') nem érvényes állapot!"
                )

        transitions = {}
        for line_num, line in enumerate(lines[4:], start=5):
            parts = line.split()
            if len(parts) != 3:
                raise ValueError(
                    f"Hibás átmenet formátum a {line_num}. sorban: '{line}'"
                )

            src, sym, dst = parts

            if src not in valid_states_set:
                raise ValueError(
                    f"A(z) {line_num}. sorban a forrásállapot ('{src}') nem érvényes!"
                )
            if sym not in set(alphabet):
                raise ValueError(
                    f"A(z) {line_num}. sorban a szimbólum ('{sym}') nem szerepel az ábécében!"
                )
            if dst not in valid_states_set:
                raise ValueError(
                    f"A(z) {line_num}. sorban a célállapot ('{dst}') nem érvényes!"
                )
            transitions.setdefault((src, sym), set()).add(dst)

        return valid_states, alphabet, start_state, final_states, transitions

    def determinize(
            self, valid_states, alphabet, start_state, final_states, transitions
    ):
        start_tuple = tuple(sorted([start_state]))

        queue = deque([start_tuple])
        set_to_name = {start_tuple: "s0"}
        dfa_states_order = [start_tuple]
        dfa_transitions = []

        while queue:
            curr_tuple = queue.popleft()
            curr_name = set_to_name[curr_tuple]

            for sym in alphabet:
                next_set = set()
                for q in curr_tuple:
                    next_set.update(transitions.get((q, sym), []))
                if not next_set:
                    continue

                next_tuple = tuple(sorted(next_set))
                if next_tuple not in set_to_name:
                    name = f"s{len(set_to_name)}"
                    set_to_name[next_tuple] = name
                    dfa_states_order.append(next_tuple)
                    queue.append(next_tuple)

                dfa_transitions.append(
                    (curr_name, sym, set_to_name[next_tuple])
                )

        all_dfa_state_names = [set_to_name[st] for st in dfa_states_order]

        dfa_finals = []
        for st in dfa_states_order:
            if any(q in final_states for q in st):
                dfa_finals.append(set_to_name[st])

        def state_index(s_name):
            return int(s_name[1:])

        dfa_transitions.sort(
            key=lambda x: (
                state_index(x[0]),
                alphabet.index(x[1]) if x[1] in alphabet else x[1],
                state_index(x[2]),
            )
        )

        return all_dfa_state_names, dfa_finals, dfa_transitions

    def write_output(
            self,
            target,
            dfa_states,
            alphabet,
            start_state_name,
            dfa_finals,
            dfa_transitions,
    ):
        lines = [
            " ".join(dfa_states),
            " ".join(alphabet),
            start_state_name,
            " ".join(dfa_finals),
        ]
        for src, sym, dst in dfa_transitions:
            lines.append(f"{src} {sym} {dst}")

        output_str = "\n".join(lines) + "\n"

        if target is None or target == "-":
            sys.stdout.write(output_str)
        else:
            output_dir = Path(target).parent
            if output_dir and not output_dir.exists():
                output_dir.mkdir(parents=True, exist_ok=True)
            with open(target, "w", encoding="utf-8") as f:
                f.write(output_str)


if __name__ == "__main__":
    problem = AutomatonDeterminizationProblem()
    test_cases = [
        ("hazi2txtk/hazi2bement1.txt", "hazi2txtk/output1.txt"),
        ("hazi2txtk/hazi2bement2.txt", "hazi2txtk/output2.txt"),
        ("hazi2txtk/hazi2bement3.txt", "hazi2txtk/output3.txt"),
        ("hazi2txtk/hazi2bement4.txt", "hazi2txtk/output4.txt"),
    ]

    print("=== Saját tesztek futtatása a helyi mappákra ===")
    for input_file, output_file in test_cases:
        try:
            problem.process_file(input_file, output_file)
            print(f"  -> Sikeresen lefutott: {input_file}")
        except Exception as e:
            print(f"  -> Hiba ennél: {input_file}: {e}")