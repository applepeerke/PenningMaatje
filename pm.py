#!/usr/bin/python3
import datetime
import getopt
import os
import sys

from src.DL.Enums.Enums import Summary
from src.GL.Const import QUIT, EMPTY
from src.GL.Enums import Color
from src.GL.GeneralException import GeneralException
from src.GL.Validate import normalize_dir, isInt, toBool, isPathname
from src.pmc import PMC

# Parameters
input_dir = EMPTY
output_dir = EMPTY
year = None
build = False
summary_type = Summary.AnnualAccountPlus
template_name = None

usage = 'usage: pm.py -i <inputdir> -o <outputdir> -y <year> -b <build> -s <summarytype> -t <templatename> -h'
errorText = Color.RED + "Error:" + Color.NC + " "


# ---------------------------------------------------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------------------------------------------------


def main(argv):
    global input_dir, output_dir, year, build, summary_type, template_name

    try:
        opts, args = getopt.getopt(
            argv, "b:h:i:o:s:t:y:",
            [
                "bbuild=",
                "iinputdir=",
                "ooutputdir=",
                "ssummarytype=",
                "ttemplatename=",
                "yyear="
             ])
    except getopt.GetoptError:
        sys.exit(2)

    for opt, arg in opts:
        if opt == "-h":
            try:
                text_file = open("help.txt", "r")
                lines = text_file.readlines()
                for line in lines:
                    print(line.rstrip('\r\n'))
                text_file.close()
            except IOError:
                print(usage)
            sys.exit(0)

        elif opt in ("-i", "--inputdir"):
            input_dir = normalize_dir(arg, False)
            if input_dir == QUIT or not os.path.isdir(input_dir):
                exit_program('Parameter -i (input directory) is not valid or does not exist.')

        elif opt in ("-o", "--outputdir"):
            output_dir = normalize_dir(arg, False)
            if output_dir == QUIT or not os.path.isdir(output_dir):
                exit_program('Parameter -i (output_dir directory) is not valid or does not exist.')

        elif opt in ("-y", "--year"):
            year = arg
            if not isInt(year) or not 1900 < int(year) < 2100:
                exit_program('Parameter -y (year) is not valid.')

        elif opt in ("-b", "--build"):
            build = arg
            if not toBool(build) in (True, False):
                exit_program('Parameter -b (build) is not valid.')

        elif opt in ("-s", "--summarytype"):
            summary_type = arg
            if summary_type not in Summary.values():
                exit_program(f'Parameter -t (summary type) is not valid. it must be one of {Summary.values()}')

        elif opt in ("-t", "--templatename"):
            template_name = arg
            if not isPathname(template_name):
                exit_program(f'Parameter -t (template name) is not valid.')

    try:
        if not year:
            year = datetime.datetime.now().year
        template_names = {summary_type: template_name} if template_name else {}

        pmc = PMC(output_dir=output_dir, year=year, build=build, input_dir=input_dir)
        pmc.create_summary(summary_type, year, template_names=template_names)

    except GeneralException as e:
        exit_program(e.message)

    exit_program()


def exit_program(error_text=EMPTY):
    if error_text:
        print(f'\n{errorText} {error_text}')
        print(usage)
        print('use parameter "-h" for help.')
    sys.exit(0)


# ---------------------------------------------------------------------------------------------------------------------
# M a i n l i n e
# ---------------------------------------------------------------------------------------------------------------------


if __name__ == "__main__":
    main(sys.argv[1:])
