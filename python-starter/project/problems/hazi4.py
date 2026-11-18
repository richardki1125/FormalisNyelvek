import argparse
from collections import Counter
from pathlib import Path
import re
import sys
from project.problem import Problem


class RegexLogProblem(Problem):

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
        head = r"^[0-9-]+ [0-9:.]+ +[0-9]+ +[0-9]+"

        if subtask == 1:
            patterns = [
                # 1.1: összes sor, amelyik 10. hónap 15-én jött létre
                r"^10-15\b",
                # 1.2: összes sor, amelyik 10. hónap 15-én 10:18:51-kor jött létre
                r"^10-15 10:18:51\b",
                # 1.3: összes sor, amelyik 51 másodperckor jött létre (mindegy a perc)
                r"^[0-9-]+ [0-9]{2}:[0-9]{2}:51\b",
                # 1.4: összes lowmemorykiller taget tartalmazó sor
                rf"{head} [IDVEFAW] +\blowmemorykiller *:",
                # 1.5: összes 10:18:51-kor keletkező 221-es PID-jú sor
                r"^[0-9-]+ 10:18:51\b(?:\.[0-9]+)? +221 +[0-9]+\b",
                # 1.6: összes hibát tartalmazó sor (E)
                rf"{head} E ",
                # 1.7: összes warning (W), amit a PackageManager küld
                rf"{head} W +\bPackageManager *:",
                # 1.8: összes ExoPlayer-es debug (D) infó
                rf"{head} D +[^:\r\n]*ExoPlayer[^:\r\n]*:",
                # 1.9: összes java állomány pozíciót tartalmazó hiba és warning (EW .java:)
                rf"{head} [EW] .+?\.java:",
                # 1.10: összes sor, ami tartalmazza a Thread szót a message részben (nem a tagben)
                rf"{head} [IDVEFAW] .+?:.*Thread",
            ]
            return [
                str(len(re.findall(pat, content, re.MULTILINE))) for pat in patterns
            ]

        if subtask == 2:
            java_files = []
            error_messages = re.findall(
                rf"{head} E .+?:(.*)$", content, re.MULTILINE
            )
            for msg in error_messages:
                java_files.extend(re.findall(r"([^\s(:]+\.java):", msg))
            return java_files

        if subtask == 3:
            pids = re.findall(
                r"^[0-9-]+ [0-9:.]+ +([0-9]+) +[0-9]+ [IDVEFAW] ",
                content,
                re.MULTILINE,
            )
            return list(dict.fromkeys(pids))

        if subtask == 4:
            error_pids = re.findall(
                r"^[0-9-]+ [0-9:.]+ +([0-9]+) +[0-9]+ E ",
                content,
                re.MULTILINE,
            )
            if not error_pids:
                return ["PID=0 (0 errors)"]
            top_pid, top_count = Counter(error_pids).most_common(1)[0]
            return [f"PID={top_pid} ({top_count} errors)"]

        if subtask == 5:
            matches = re.findall(
                r"^[0-9-]+ [0-9:.]+ +([0-9]+) +\1 E ",
                content,
                re.MULTILINE,
            )
            return [str(len(matches))]

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
        ("hazi4txtk/hazi4bemenet.txt", "hazi4txtk/output1.txt", 1),
    ]

    print("=== Saját tesztek futtatása a helyi mappákra ===")
    for input_file, output_file, subtask in test_cases:
        try:
            problem.process_file(input_file, output_file, subtask)
            print(f"  -> Sikeresen lefutott (--rgx {subtask}): {output_file}")
        except Exception as e:
            print(f"  -> Hiba ennél (--rgx {subtask}, {input_file}): {e}")