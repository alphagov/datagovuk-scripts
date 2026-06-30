# Playbook for soft deleting broken resource links

1. Count active resources
2. Run a final broken links retry
3. Filter out deferred orgs
4. Upload to S3
5. Run the deletion and SOLR reindex script

The below are instructions to soft delete broken resource links from our database.

## Count active resources

1. Find the CKAN app pod

    `$ kubectl get pods -n datagovuk-<env>`

2. Execute a shell into it

    `$ kubectl exec -it <ckan-pod-name> -n datagovuk-<env> -- bash`

3. Connect to the postgres db e.g. `psql -U ckan`

4. Execute the below sql

    ```sql
    select count(*) from resource join package on resource.package_id = package.id where package.state = 'active' and resource.state = 'active';
    ```

5. Note down the count of active resources.

## Run a final broken links retry

This is so that our "to delete" spreadsheet is as up to date as possible.

1. Execute a shell onto the CKAN pod

2. Run the check links script in dry-run verbose mode:

    ```bash
        $ python check_links.py --mode dry-run --verbose
    ```

3. Download the report CSV — this becomes the input for the "Filter out deferred orgs" step.

4. Re-run the transient errors script

## Filter out deferred orgs

> **prerequisites:**
>
> ⚠️ Use the verified broken links CSV from the Transient errors script.

1. Go to `datagovuk-scripts/check-links-transient`

    - Use the broken links csv that we ran all the transient error runs on

    - Filter out organisations that have opted out

2. Run the filter deferred orgs script and provide a list of excluded / deferred orgs e.g. --exclude example-org

    ```bash
    $ scripts/filter.py [broken links csv] [output file path e.g. broken_links_to_delete_20260619T0801.csv] --exclude abc-agency,def-agency​
    ```

    ⚠️ output file name must be like `broken_links_to_delete_$TIMESTAMP.csv`

    > `$TIMESTAMP is from check reports github repo

3. Conirm the count of filtered orgs match by running:

    ```sql
    select count(*) from resource join package on resource.package_id = package.id where package.state = 'active' and resource.state = 'active';
    ```

4. Upload the filtered out broken links csv ( `broken_links_to_delete_$TIMESTAMP.csv` ) to this repo `datagovuk-scripts/check-links/broken_links_to_delete_$TIMESTAMP.csv`

## Running the deletion + reindex script

1. Create a PR to update the `checklinks.report.timestamp` in `values-[env].yml` in `govuk-dgu-charts` to the timestamp of the file e.g. `20260619T0801`

2. Communicate to the team channel that you'll be running the deletion script on [environment]

3. Merge PR

4. Run the Cron Job manually

    `kubectl create job --from=cronjob/ckan-check-links-process [test-check-links-process-deletion-260626] -n datagovuk`

5. Monitor the cron-job in ARGO

## Post live verification

- Verify number of active resources with the same SQL as earlier

    ```sql
    select count(*) from resource join package on resource.package_id = package.id where package.state='active' and resource.state = 'active';
    ```

- Check a sample of records in the database to confirm they have been soft deleted

- After the SOLR index completes, verify on the [environment].data.gov.uk that the resource is no longer being displayed on the dataset/package. Perhaps use a sample of 3 or 4 datasets to verify.
