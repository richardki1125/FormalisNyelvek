from pathlib import Path
from project.problem import Problem


class DFA(Problem):

    def initialize_parser(self, parser):
        try:
            parser.add_argument(
                "--check",
                help="Az ellenőrizendő szó vagy szavak",
            )
        except Exception:
            pass

    def is_chosen_problem(self, args):
        return getattr(args, "check", None) is not None

    def run(self, args):
        self.process_file(args.input, args.output, args.check)

    def process_file(self, input_path, output_path, check_words: str):
        states, alphabet, start_state, final_states, transitions = self.read_automaton(
            input_path
        )
        words = check_words.split(",")
        results = []
        for word in words:
            if self.accepts(word, start_state, final_states, transitions):
                results.append("IGEN")
            else:
                results.append("NEM")

        output_dir = Path(output_path).parent
        if output_dir and not output_dir.exists():
            output_dir.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as output_file:
            output_file.write("\n".join(results) + "\n")

    def read_automaton(self, filename):
        with open(filename, "r", encoding="utf-8") as input_file:
            lines = [line.rstrip("\r\n") for line in input_file]

        while len(lines) > 4 and not lines[-1].strip():
            lines.pop()

        states = set(lines[0].split())
        alphabet = set(lines[1].split())
        start_state = lines[2].strip()
        final_states = set(lines[3].split())

        transitions = {}
        for line in lines[4:]:
            if not line.strip():
                continue
            source, symbol, destination = line.split()
            transitions[(source, symbol)] = destination

        return states, alphabet, start_state, final_states, transitions

    def accepts(self, word, start_state, final_states, transitions):
        current_state = start_state

        for symbol in word:
            key = (current_state, symbol)
            if key not in transitions:
                return False
            current_state = transitions[key]

        return current_state in final_states


if __name__ == "__main__":
    problem = DFA()
    test_cases = [
        ("hazi1txtk/input_file1.txt", "hazi1txtk/output1.txt"),
        ("hazi1txtk/input_file2.txt", "hazi1txtk/output2.txt"),
    ]

    print("=== Saját tesztek futtatása a helyi mappákra ===")
    for input_file, output_file in test_cases:
        try:
            words = input(f"Add meg az ellenőrizendő szót/szavakat ({input_file}): ")
            problem.process_file(input_file, output_file, words)
            print(f"  -> Sikeresen lefutott: {input_file} -> {output_file}")
        except Exception as e:
            print(f"  -> Hiba ennél: {input_file}: {e}")