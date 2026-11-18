import argparse
from collections import deque
from pathlib import Path
import re
import sys
from project.problem import Problem


class AutomatonMinimizationProblem(Problem):

    def initialize_parser(self, parser: argparse.ArgumentParser):
        try:
            parser.add_argument(
                "--mini",
                action="store_true",
                help="Kapcsoló az automata minimalizálásának elvégzéséhez",
            )
        except argparse.ArgumentError:
            pass

    def is_chosen_problem(self, args) -> bool:
        return (
                getattr(args, "mini", False)
                or str(getattr(args, "problem", "")) == "3"
        )

    def run(self, args):
        input_source = getattr(args, "input", None)
        output_target = getattr(args, "output", None)
        self.process_file(input_source, output_target)

    def process_file(self, input_path, output_path):
        valid_states, alphabet, start_state, final_states, transitions = (
            self.load_dfa(input_path)
        )

        min_states, min_start, min_finals, min_transitions = self.minimize(
            valid_states, alphabet, start_state, final_states, transitions
        )

        self.write_output(
            output_path,
            min_states,
            alphabet,
            min_start,
            min_finals,
            min_transitions,
        )

    def load_dfa(self, source):
        if source is None or source == "-":
            raw_lines = [line.rstrip("\r\n") for line in sys.stdin]
        elif isinstance(source, (str, Path)):
            path = Path(source)
            if not path.exists():
                raise FileNotFoundError(f"A fájl nem található: {source}")
            with open(path, "r", encoding="utf-8") as f:
                raw_lines = [line.rstrip("\r\n") for line in f]
        else:
            raw_lines = [line.rstrip("\r\n") for line in source]

        # A fájl végi üres sorok eltávolítása (az esetleges üres 4. sort megőrizve)
        while len(raw_lines) > 4 and not raw_lines[-1].strip():
            raw_lines.pop()

        if len(raw_lines) < 4:
            raise ValueError(
                "A bemeneti fájl nem tartalmazza a szükséges 4 soros fejlécet!"
            )

        valid_states = raw_lines[0].split()
        if not valid_states:
            raise ValueError("Az állapotok listája nem lehet üres!")
        valid_states_set = set(valid_states)

        alphabet = raw_lines[1].split()
        if not alphabet:
            raise ValueError("Az ábécé nem lehet üres!")
        alphabet_set = set(alphabet)

        start_state = raw_lines[2].strip()
        if start_state not in valid_states_set:
            raise ValueError(
                f"A kezdőállapot ('{start_state}') nem érvényes állapot!"
            )

        final_states = set(raw_lines[3].split())
        for fs in final_states:
            if fs not in valid_states_set:
                raise ValueError(
                    f"A végállapot ('{fs}') nem érvényes állapot!"
                )

        transitions = {}
        for line_num, line in enumerate(raw_lines[4:], start=5):
            if not line.strip():
                continue
            parts = line.split()
            if len(parts) != 3:
                raise ValueError(
                    f"Hibás átmenet formátum a(z) {line_num}. sorban: '{line}'"
                )

            src, sym, dst = parts

            if src not in valid_states_set:
                raise ValueError(
                    f"A(z) {line_num}. sorban a forrásállapot ('{src}') nem érvényes!"
                )
            if sym not in alphabet_set:
                raise ValueError(
                    f"A(z) {line_num}. sorban a szimbólum ('{sym}') nem szerepel az ábécében!"
                )
            if dst not in valid_states_set:
                raise ValueError(
                    f"A(z) {line_num}. sorban a célállapot ('{dst}') nem érvényes!"
                )

            if (src, sym) in transitions and transitions[(src, sym)] != dst:
                raise ValueError(
                    f"Nem determinisztikus átmenet a(z) {line_num}. sorban: ({src}, {sym})"
                )

            transitions[(src, sym)] = dst

        return valid_states, alphabet, start_state, final_states, transitions

    def minimize(
            self, valid_states, alphabet, start_state, final_states, transitions
    ):
        def state_num(state_name: str) -> int:
            match = re.search(r"(\d+)$", state_name)
            if match:
                return int(match.group(1))
            return valid_states.index(state_name)

        # 1. Elérhető állapotok meghatározása a kezdőállapotból (BFS)
        visited = {start_state}
        queue = deque([start_state])
        while queue:
            curr = queue.popleft()
            for sym in alphabet:
                nxt = transitions.get((curr, sym))
                if nxt is not None and nxt not in visited:
                    visited.add(nxt)
                    queue.append(nxt)

        reachable = [st for st in valid_states if st in visited]

        # 2. Kezdeti partíció: végállapotok és nem végállapotok
        accepting = frozenset(st for st in reachable if st in final_states)
        non_accepting = frozenset(st for st in reachable if st not in final_states)
        partitions = [grp for grp in (accepting, non_accepting) if grp]

        # 3. Partíciófinomítás, amíg már egyik csoport sem esik szét
        while True:
            state_to_group = {
                st: idx
                for idx, grp in enumerate(partitions)
                for st in grp
            }
            new_partitions = []

            for grp in partitions:
                if len(grp) <= 1:
                    new_partitions.append(grp)
                    continue

                subgroups = {}
                for st in grp:
                    signature = tuple(
                        state_to_group.get(transitions.get((st, sym)))
                        for sym in alphabet
                    )
                    subgroups.setdefault(signature, []).append(st)

                for sub in subgroups.values():
                    new_partitions.append(frozenset(sub))

            if len(new_partitions) == len(partitions):
                break
            partitions = new_partitions

        # 4. Összevont állapotok átnevezése a legkisebb sorszámú tag alapján (s<index>)
        old_to_new = {}
        new_state_names = []
        for grp in partitions:
            smallest_state = min(grp, key=state_num)
            new_name = f"s{state_num(smallest_state)}"
            new_state_names.append(new_name)
            for st in grp:
                old_to_new[st] = new_name

        min_states = sorted(new_state_names, key=state_num)
        min_start = old_to_new[start_state]
        min_finals = sorted(
            {old_to_new[st] for st in reachable if st in final_states},
            key=state_num,
        )

        # 5. Átmenetek felépítése duplikációk nélkül, rendezve
        min_transitions_set = set()
        for st in reachable:
            src_new = old_to_new[st]
            for sym in alphabet:
                dst_old = transitions.get((st, sym))
                if dst_old is not None and dst_old in old_to_new:
                    dst_new = old_to_new[dst_old]
                    min_transitions_set.add((src_new, sym, dst_new))

        min_transitions = sorted(
            min_transitions_set,
            key=lambda t: (state_num(t[0]), t[1], state_num(t[2])),
        )

        return min_states, min_start, min_finals, min_transitions

    def write_output(
            self,
            target,
            min_states,
            alphabet,
            min_start,
            min_finals,
            min_transitions,
    ):
        lines = [
            " ".join(min_states),
            " ".join(alphabet),
            min_start,
            " ".join(min_finals),
        ]
        for src, sym, dst in min_transitions:
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
    problem = AutomatonMinimizationProblem()
    test_cases = [
        ("hazi3txtk/hazi3bemenet.txt", "hazi3txtk/output1.txt"),
        ("hazi3txtk/hazi3bemenet2.txt", "hazi3txtk/output2.txt"),
        ("hazi3txtk/hazi3bemenet3.txt", "hazi3txtk/output3.txt"),
    ]

    print("=== Saját tesztek futtatása a helyi mappákra ===")
    for input_file, output_file in test_cases:
        try:
            problem.process_file(input_file, output_file)
            print(f"  -> Sikeresen lefutott: {input_file}")
        except Exception as e:
            print(f"  -> Hiba ennél: {input_file}: {e}")