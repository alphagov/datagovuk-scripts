import argparse
import boto3
from datetime import UTC, datetime
import json
import os
import logging
import psycopg2
import pysolr
import re
import subprocess


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


def get_all_medin_datasets():
    solr_url = os.getenv('CKAN_SOLR_URL')
    solr = pysolr.Solr(solr_url, timeout=10)

    ping = solr.ping()
    resp = json.loads(ping)
    if resp.get('status') == 'OK':
        return solr.search(
                    'organization: "marine-environmental-data-information-network"',
                    **{
                        "fq": [],
                        "fl": "id,extras_guid,metadata_modified,title",
                        "sort": "extras_guid asc, metadata_modified desc",
                        "start": 0,
                        "rows": 5000,
                    },
                )
    else:
        raise Exception(f"Solr response not OK: {resp.get('status')}")


def get_datasets_to_remove(datasets):
    datasets_to_remove = []
    last_guid = None

    with psycopg2.connect(os.getenv('CKAN_SQLALCHEMY_URL')) as conn:
        cursor = conn.cursor()

        for dataset in datasets:
            cursor.execute(f"SELECT id FROM package WHERE id = '{dataset.get('id')}'")
            in_database = cursor.fetchone() != None
            if last_guid is not None and dataset.get('extras_guid') == last_guid:
                datasets_to_remove.append((dataset.get('id'), dataset.get('extras_guid'), in_database))
            elif not in_database:
                datasets_to_remove.append((dataset.get('id'), dataset.get('extras_guid'), in_database))
            last_guid = dataset.get('extras_guid')

    return datasets_to_remove


def remove_datasets(logger, datasets_to_remove, solr_only):
    datasets_deleted_from_db = datasets_deleted_from_solr = 0

    logger.info(f"{len(datasets_to_remove)} duplicate datasets to remove")
    for i, (dataset_id, guid, in_database) in enumerate(datasets_to_remove):
        logger.info(f"Removing dataset {i+1}: ID: {dataset_id}, GUID: {guid}")
        if in_database and not solr_only:
            try:
                command = ["ckan", "dataset", "delete", dataset_id]
                subprocess.check_call(command)
                datasets_deleted_from_db += 1
            except Exception as exc:
                logger.error(f"Error occurred while deleting dataset from database, {dataset_id}: {exc}")
        try:
            command = ["ckan", "search-index", "clear", dataset_id]
            subprocess.check_call(command)
            datasets_deleted_from_solr += 1
        except Exception as exc:
            logger.error(f"Error while removing dataset from solr, {dataset_id}: {exc}")
        break

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
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M")
    log_path = os.path.join(args.log_dir, f"remove_duplicate_solr_datasets_{timestamp}.log")
    logger = setup_logging(log_path)
    logger.info("===== settings =====")
    logger.info(f"Log path: {log_path}")
    logger.info(f"Solr only: {args.solr_only}")
    logger.info("====================")

    medin_datasets = get_all_medin_datasets()
    datasets_to_remove = get_datasets_to_remove(medin_datasets)
    remove_datasets(logger, datasets_to_remove, args.solr_only)
    upload_log_to_s3(log_path, "remove_duplicates")


main()
