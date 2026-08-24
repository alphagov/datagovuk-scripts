import argparse
import boto3
from datetime import UTC, datetime
import json
import os
import logging
import psycopg2
import pysolr
import subprocess
import sys


bucket = None


def setup_logging(log_path: str) -> logging.Logger:
    logger = logging.getLogger(__name__)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    console = logging.StreamHandler()
    console.setFormatter(fmt)
    logger.addHandler(console)
    if log_path:
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(fmt)
        logger.addHandler(file_handler)
    return logger


def get_org_datasets(org_name):
    solr_url = os.getenv('CKAN_SOLR_URL')
    solr = pysolr.Solr(solr_url, timeout=10)

    ping = solr.ping()
    resp = json.loads(ping)
    if resp.get('status') == 'OK':
        datasets = solr.search(
                    f'organization: {org_name}',
                    **{
                        "fq": [],
                        "fl": "id,extras_guid,metadata_modified,title",
                        "sort": "title asc, extras_guid asc, metadata_modified desc",
                        "start": 0,
                        "rows": 5000,
                    },
                )

        # sort by metadata modified in reverse as assuming we want to keep the latest and delete the older dataset
        datasets_sorted = sorted(datasets.docs, key=lambda x: x.get('metadata_modified', ''), reverse=True)
        # sort by title first as the solr sort was not keeping the sort order
        return sorted(datasets_sorted, key=lambda x: (x.get('title'), x.get('extras_guid', '')))
    else:
        raise Exception(f"Solr response not OK: {resp.get('status')}")


def get_datasets_to_remove(logger, datasets):
    datasets_to_remove = []
    last_guid = None
    last_title = None

    with psycopg2.connect(os.getenv('CKAN_SQLALCHEMY_URL')) as conn:
        cursor = conn.cursor()

        for dataset in datasets:
            logger.info(f"GUID: {dataset.get('extras_guid')}, title: {dataset.get('title')}, metadata modified: {dataset.get('metadata_modified')}")
            cursor.execute(f"SELECT id FROM package WHERE id = '{dataset.get('id')}'")
            in_database = cursor.fetchone() != None
            if (last_title and not last_guid and dataset.get('title') == last_title) or \
                (last_guid and dataset.get('extras_guid') == last_guid) or \
                not in_database:
                datasets_to_remove.append((dataset.get('id'), dataset.get('extras_guid'), dataset.get('title'), in_database, not last_guid))
            last_guid = dataset.get('extras_guid', None)
            last_title = dataset.get('title', None)

    return datasets_to_remove


def remove_datasets(logger, datasets_to_remove, report_only, solr_only):
    datasets_deleted_from_db = datasets_deleted_from_solr = 0

    logger.info(f"{len(datasets_to_remove)} duplicate datasets to remove")
    for i, (dataset_id, guid, title, in_database, no_guid) in enumerate(datasets_to_remove):
        logger.info(f"{'Will remove' if report_only else 'Removing'} dataset {i+1}: ID: {dataset_id}, GUID: {guid}, title: {title}{', missing guid' if no_guid else ''} from Solr{' and database' if in_database else ''} ")

        if not report_only:
            if in_database and not solr_only:
                try:
                    command = ["ckan", "dataset", "delete", dataset_id]
                    # subprocess.check_call(command)
                    datasets_deleted_from_db += 1
                except Exception as exc:
                    logger.error(f"Error occurred while deleting dataset from database, {dataset_id}: {exc}")
            try:
                command = ["ckan", "search-index", "clear", dataset_id]
                # subprocess.check_call(command)
                datasets_deleted_from_solr += 1
            except Exception as exc:
                logger.error(f"Error while removing dataset from solr, {dataset_id}: {exc}")

    if not report_only:
        logger.info(f"Successfully deleted from solr: {datasets_deleted_from_solr}, db: {datasets_deleted_from_db}")


def upload_log_to_s3(path, s3_path=None):
    bucket_name = os.environ.get("CKAN_OUTPUT_BUCKET_NAME")
    if not bucket_name:
        raise Exception("CKAN_OUTPUT_BUCKET_NAME environment variable is not set")

    s3 = boto3.resource("s3")
    bucket = s3.Bucket(bucket_name)

    s3_path = s3_path + "/" + path.split("/")[-1]
    bucket.upload_file(path, s3_path)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--org",
        "-o",
        default="",
        help="Organisation to remove duplicates for",
    )
    parser.add_argument(
        "--log-dir",
        "-l",
        default=".",
        help="Log file report for duplicate datasets removed",
    )
    parser.add_argument(
        "--solr-only",
        "-s",
        default=True,
        help="Only remove solr datasets (default True)",
    )
    parser.add_argument(
        "--report-only",
        "-r",
        default=True,
        help="Only remove solr datasets (default True)",
    )

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)        

    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M")
    log_path = os.path.join(args.log_dir, f"remove_duplicate_datasets_{timestamp}.log")
    logger = setup_logging(log_path)
    logger.info("===== settings =====")
    logger.info(f"Log path: {log_path}")
    logger.info(f"Solr only: {args.solr_only}")
    logger.info(f"Report only: {args.report_only}")
    logger.info("====================")

    if not args.org:
        logger.error("Target organisation not defined, use -o <org> or --org <org> to pass it in")
        return 1

    try:
        org_datasets = get_org_datasets(args.org)
        datasets_to_remove = get_datasets_to_remove(logger, org_datasets)
        remove_datasets(logger, datasets_to_remove, args.report_only, args.solr_only)
        print(f"Logs written to {log_path}")
        upload_log_to_s3(log_path, "remove_duplicates")
    except Exception as e:
        logger.error(str(e))
        return 1


sys.exit(main())
