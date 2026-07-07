import argparse
import csv
from collections import defaultdict
from pprint import pprint


def analyse(csv_file_path):
    ok_statuses = set()
    success_urls = []
    error_urls = []
    retry_urls = set()
    total_urls = 0
    error_breakdown = defaultdict(int)
    success_breakdown = defaultdict(int)
    org_breakdown = defaultdict(int)

    with open(csv_file_path, "r") as f:
        reader = csv.DictReader(f)

        for row in reader:
            total_urls += 1
            if row["category"] == "OK":
                ok_statuses.add(row["http-status"])
                success_urls.append(row["resource-url"])
                success_breakdown[row["http-status"]] += 1
            else:
                error_urls.append(row["resource-url"])
                error_key = row["http-status"]
                if not error_key:
                    error_key = row["category"]
                if error_key != "DNS_ERROR":
                    retry_urls.add(row["resource-url"])
                    org_breakdown[row["org-name"]] += 1
                error_breakdown[error_key] += 1

    count_success_urls = len(success_urls)

    print(f"ok_statuses: {ok_statuses}")
    print(f"Total urls: {total_urls}")
    count_success_urls = len(success_urls)
    print(
        f"Success urls: {count_success_urls} ({((count_success_urls / total_urls) * 100):.2f}%)"
    )
    count_error_urls = len(error_urls)
    print(
        f"Error urls: {count_error_urls} ({((count_error_urls / total_urls) * 100):.2f}%)"
    )

    print()
    print("Error breakdown:")
    sorted_error_breakdown = sorted(
        list(error_breakdown.items()), key=lambda x: x[1], reverse=True
    )
    for error_type, error_count in sorted_error_breakdown:
        print(
            f"{error_type}: {error_count} {((error_count / count_error_urls) * 100):.2f}%"
        )
    print()

    biggest_orgs = sorted(
        list(org_breakdown.items()), key=lambda x: x[1], reverse=True
    )[:10]
    print("Biggest orgs")
    pprint(biggest_orgs)


def main():
    parser = argparse.ArgumentParser(
        description="A script to analyse broken link CSVs for data.gov.uk"
    )
    parser.add_argument("file_path", type=str, help="The CSV file to analyse")
    args = parser.parse_args()
    analyse(args.file_path)


if __name__ == "__main__":
    main()
