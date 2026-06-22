# Datagovuk Scripts

A collection of datagovuk scripts that are run ad-hoc on your machine or on a container. Please read the README.md in each directory for more information on how to run the scripts.

## check-links

Python scripts used to check for broken links, generate reports and remove them from the system.

## search-analytics

Node script used to export search analytc reports into CSV and Excel files.

## Running the docker stack

1. Clone https://github.com/alphagov/ckanext-datagovuk#running-ckan-and-find-locally
2. Run the CKAN docker compose stack locally

Run an AWS local stack container as it's required for the scripts

```bash
 docker run --rm -d --name floci -p 4566:4566 \
   -v /var/run/docker.sock:/var/run/docker.sock \
   floci/floci:latest
```

Create an S3 bucket to be used by the check-links scripts

```bash
aws --endpoint-url=http://localhost:4566 s3 mb s3://ckan-output-bucket
```

Set the AWS credentials in the .env file

```bash
AWS_ENDPOINT_URL=http://localhost:4566
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
CKAN_OUTPUT_BUCKET_NAME=ckan-output-bucket
```

Run the docker compose local stack from the root directory:

```bash
docker compose up
```
