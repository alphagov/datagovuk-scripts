import argparse
import csv
from collections import defaultdict

def is_row_excluded(row, exclusions, exclusion_substrings):
    for exclusion_column, exclusion_values in exclusions.items():
        for exclusion_value in exclusion_values:
            if row[exclusion_column] == exclusion_value:
                return True
    for exclusion_column, exclusion_values in exclusion_substrings.items():
        for exclusion_value in exclusion_values:
            if exclusion_value in row[exclusion_column]:
                return True
    return False


def filter(input_file_path, output_file_path, exclusions, exclusion_substrings):
    with open(input_file_path, "r") as input_file:
        reader = csv.DictReader(input_file)
        with open(output_file_path, "w") as output_file:
            writer = csv.DictWriter(output_file, fieldnames=reader.fieldnames)
            writer.writeheader()
            for row in reader:
                if is_row_excluded(row, exclusions, exclusion_substrings):
                    continue
                writer.writerow(row)


def main():
    parser = argparse.ArgumentParser(description="A script to filter broken link CSVs for data.gov.uk")
    parser.add_argument("input_file_path", type=str, help="The CSV file to filter")
    parser.add_argument("output_file_path", type=str, help="The file path to write the filtered CSV to")
    parser.add_argument("-e", "--exclude", action="append", type=str, help="The column(s)/values to exclude")
    parser.add_argument("-ei", "--exclude-substring", action="append", type=str, help="The column(s)/values to exclude if exclusion value is a substring of a particular row's value")
    args = parser.parse_args()
    exclusions = {}
    for exclude_argument in args.exclude:
        try:
            column_name, value = exclude_argument.split("=")
        except ValueError:
            raise Exception(f"--exclude argument {exclude_argument} did not follow <column>=<value> pattern")
        if "," in value:
            value = value.split(",")
        else:
            value = [value]
        exclusions[column_name] = value
    exclusion_substrings = {}
    for exclude_argument in args.exclude_substring:
        try:
            column_name, value = exclude_argument.split("=")
        except ValueError:
            raise Exception(f"--exclude-substring argument {exclude_argument} did not follow <column>=<value> pattern")
        if "," in value:
            value = value.split(",")
        else:
            value = [value]
        exclusion_substrings[column_name] = value
    filter(args.input_file_path, args.output_file_path, exclusions, exclusion_substrings)


if __name__ == "__main__":
    main()
