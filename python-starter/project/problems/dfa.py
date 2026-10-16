from project.problem import Problem

class DFA(Problem):

    def initialize_parser(self, parser):
        parser.add_argument(
            '--check',
            help='Az ellenőrizendő szó vagy szavak'
        )

    def is_chosen_problem(self, args):
        return args.check is not None

    def run(self, args):
        states, alphabet, start_state, final_states, transitions = self.read_automaton(
            args.input
        )
        words = args.check.split(',')
        results = []
        for word in words:
            if self.accepts(
                    word,
                    start_state,
                    final_states,
                    transitions
            ):
                results.append("IGEN")
            else:
                results.append("NEM")
        with open(args.output, "w", encoding="utf-8") as output_file:
            output_file.write("\n".join(results))

    def read_automaton(self, filename):
        with open(filename, "r", encoding="utf-8") as input_file:
            lines = [line.strip() for line in input_file if line.strip()]
        #sor 1
        states = set(lines[0].split())
        # sor2
        alphabet = set(lines[1].split())
        # sor3
        start_state = lines[2]
        #sor4
        final_states = set(lines[3].split())
        transitions = {}
        for line in lines[4:]:
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