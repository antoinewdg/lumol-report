import subprocess
import re


# options_presentation = [
#     'pandoc',
#     'presentation.md',
#     '-o presentation.pdf',
#     '-f markdown',
#     '-t beamer',
#     '-s',
#     '--bibliography bib.bib',
#     '--csl llncs.csl',
# ]

def get_files():
    with open('SUMMARY.md') as f:
        for line in f:
            res = re.search(r'\[.*\]\((.*)\)', line)
            if res is None:
                continue
            yield res.group(1)


options_report = [
    'pandoc',
    *get_files(),
    '-o report.pdf',
    '-f markdown',
    '-t latex',
    '-s',
    '--bibliography bib.bib',
    '--csl llncs.csl',
    '--number-sections',
]


def main():
    # print(' '.join(options_report))
    subprocess.call(' '.join(options_report), shell=True)
    # subprocess.call(' '.join(options_presentation), shell=True)


if __name__ == '__main__':
    main()
