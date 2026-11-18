import argparse
from collections import Counter
from pathlib import Path
import re
import sys
from project.problem import Problem


class RegexLogProblem(Problem):
    LOGCAT_RGX = re.compile(
        r"(([0-9-]+ [0-9:.]+) +([0-9]+) +([0-9]+) ([IDVEFAW]) (.+?):(?: (.+))?)",
        re.MULTILINE,
    )

    def initialize_parser(self, parser: argparse.ArgumentParser):
        try:
            parser.add_argument(
                "--rgx",
                type=int,
                choices=[1, 2, 3, 4, 5],
                help="A megoldandó regex részfeladat sorszáma (1-5)",
            )
        except argparse.ArgumentError:
            pass

    def is_chosen_problem(self, args) -> bool:
        return (
                getattr(args, "rgx", None) is not None
                or str(getattr(args, "problem", "")) == "4"
        )

    def run(self, args):
        input_source = getattr(args, "input", None)
        output_target = getattr(args, "output", None)
        subtask = getattr(args, "rgx", None) or 1
        self.process_file(input_source, output_target, subtask)

    def process_file(self, input_path, output_path, subtask: int):
        content = self.load_content(input_path)
        output_lines = self.solve_regex_task(content, subtask)
        self.write_output(output_path, output_lines)

    def load_content(self, source) -> str:
        if source is None or source == "-":
            return sys.stdin.read()
        if isinstance(source, (str, Path)):
            path = Path(source)
            if not path.exists():
                raise FileNotFoundError(f"A fájl nem található: {source}")
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                return f.read()
        return "".join(source)

    def solve_regex_task(self, content: str, subtask: int) -> list[str]:
        # Minden illeszkedő sor: (teljes_sor, timestamp, pid, tid, level, tag, message)
        entries = self.LOGCAT_RGX.findall(content)

        if subtask == 1:
            counts = [
                # 1.1: összes sort, amelyik 10. hónap 15-én jött létre
                sum(1 for _, ts, *_ in entries if re.match(r"10-15\b", ts)),
                # 1.2: összes sort, amelyik 10. hónap 15-én 10:18:51-kor jött létre
                sum(1 for _, ts, *_ in entries if re.match(r"10-15 10:18:51\b", ts)),
                # 1.3: összes sort, amelyik 51 másodperckor jött létre (mindegy a perc)
                sum(
                    1
                    for _, ts, *_ in entries
                    if re.match(r"[0-9-]+ [0-9]{2}:[0-9]{2}:51\b", ts)
                ),
                # 1.4: összes lowmemorykiller taget tartalmazó sor
                sum(
                    1
                    for _, _, _, _, _, tag, _ in entries
                    if re.search(r"lowmemorykiller", tag)
                ),
                # 1.5: összes 10:18:51-kor keletkező 221-es process id-jú sor
                sum(
                    1
                    for _, ts, pid, *_ in entries
                    if re.search(r" 10:18:51\b", ts) and re.fullmatch(r"221", pid)
                ),
                # 1.6: összes hibát tartalmazó sor (E)
                sum(1 for _, _, _, _, lvl, _, _ in entries if re.fullmatch(r"E", lvl)),
                # 1.7: összes warning (W), amit a PackageManager küld
                sum(
                    1
                    for _, _, _, _, lvl, tag, _ in entries
                    if re.fullmatch(r"W", lvl) and re.search(r"PackageManager", tag)
                ),
                # 1.8: összes ExoPlayer-es debug (D) infó
                sum(
                    1
                    for _, _, _, _, lvl, tag, _ in entries
                    if re.fullmatch(r"D", lvl) and re.search(r"ExoPlayer", tag)
                ),
                # 1.9: összes java állomány pozíciót tartalmazó hiba és warning (EW .java:)
                sum(
                    1
                    for _, _, _, _, lvl, _, msg in entries
                    if re.fullmatch(r"[EW]", lvl) and re.search(r"\.java:", msg)
                ),
                # 1.10: összes sor, ami tartalmazza a Thread szót a message részben (nem a tagben)
                sum(
                    1
                    for _, _, _, _, _, _, msg in entries
                    if re.search(r"Thread", msg)
                ),
            ]
            return [str(c) for c in counts]

        if subtask == 2:
            java_files = []
            for _, _, _, _, lvl, _, msg in entries:
                if re.fullmatch(r"E", lvl):
                    java_files.extend(re.findall(r"([^\s(:]+\.java):", msg))
            return java_files

        if subtask == 3:
            pids = [pid for _, _, pid, *_ in entries]
            return list(dict.fromkeys(pids))

        if subtask == 4:
            error_pids = [
                pid for _, _, pid, _, lvl, _, _ in entries if re.fullmatch(r"E", lvl)
            ]
            if not error_pids:
                return ["PID=0 (0 errors)"]
            top_pid, top_count = Counter(error_pids).most_common(1)[0]
            return [f"PID={top_pid} ({top_count} errors)"]

        if subtask == 5:
            main_thread_errors = sum(
                1
                for _, _, pid, tid, lvl, _, _ in entries
                if re.fullmatch(r"E", lvl) and pid == tid
            )
            return [str(main_thread_errors)]

        raise ValueError(f"Érvénytelen --rgx érték: {subtask}")

    def write_output(self, target, lines: list[str]):
        output_str = "\n".join(str(line) for line in lines) + "\n"

        if target is None or target == "-":
            sys.stdout.write(output_str)
        else:
            output_dir = Path(target).parent
            if output_dir and not output_dir.exists():
                output_dir.mkdir(parents=True, exist_ok=True)
            with open(target, "w", encoding="utf-8") as f:
                f.write(output_str)


if __name__ == "__main__":
    problem = RegexLogProblem()
    test_cases = [
        ("hazi4txtk/hazi4bemenet.txt", "hazi4txtk/output1.txt", 1)
    ]

    print("=== Saját tesztek futtatása a helyi mappákra ===")
    for input_file, output_file, subtask in test_cases:
        try:
            problem.process_file(input_file, output_file, subtask)
            print(f"  -> Sikeresen lefutott (--rgx {subtask}): {output_file}")
        except Exception as e:
            print(f"  -> Hiba ennél (--rgx {subtask}, {input_file}): {e}")