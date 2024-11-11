#!/usr/bin/python3
import getopt
import os
import sys

from src.DL.Lexicon import ANNUAL_ACCOUNT
from src.GL.Const import QUIT, EMPTY
from src.GL.Enums import Color
from src.GL.GeneralException import GeneralException
from src.GL.Validate import normalize_dir, isInt, toBool, isFilename
from src.pmc import PMC


# Parameters
input_dir = EMPTY
output_dir = EMPTY
year = None
build = False
template_name = ANNUAL_ACCOUNT

usage = 'usage: pm.py -i <inputdir> -o <outputdir> -y <year> -b <build> -t <template> -h'
errorText = Color.RED + "Error:" + Color.NC + " "


# ---------------------------------------------------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------------------------------------------------


def main(argv):
    global input_dir, output_dir, year, build, template_name

    try:
        opts, args = getopt.getopt(
            argv, "b:h:i:o:t:y:",
            [
                "bbuild=",
                "iinputdir=",
                "ooutputdir=",
                "ttemplate=",
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

        elif opt in ("-t", "--template"):
            template_name = arg
            if not isFilename(template_name):
                exit_program('Parameter -t (template) is not valid.')

    try:
        pmc = PMC(output_dir=output_dir, year=year, build=build, input_dir=input_dir)
        pmc.produce_csv_files(template_name, year)

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
