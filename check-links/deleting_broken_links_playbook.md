# Playbook for soft deleting broken resource links in Production

1. [Count active resources](#count-active-resources)
2. [Run the broken links script for a final time](#run-the-broken-links-script-for-a-final-time)
3. [Re-run the transient errors workflow](#re-run-the-transient-errors-workflow)
4. [Filter out deferred orgs](#filter-out-deferred-orgs)
5. [Add the final report to the datagovuk-scripts repo](#add-the-final-report-to-the-datagovuk-scripts-repo)
6. [Create a PR to add the checklinksreport block to chartsapp-of-appsvalues-productionyaml](#create-a-pr-to-add-the-checklinksreport-block-to-chartsapp-of-appsvalues-productionyaml)
7. [Running the deletion script](#running-the-deletion-script)
8. [Post live verification](#post-live-verification)

The below are instructions to soft delete broken resource links from our **production database**.

## Count active resources

1. Switch your local kubernetes context to production like `kubectl config use-context govuk-production`

2. Find the CKAN app pod

    `$ kubectl get pods -n datagovuk-prod`

3. Execute a shell into it

    `$ kubectl exec -it <ckan-pod-name> -n datagovuk-prod -- bash`

4. Connect to the postgres db e.g. `psql -U ckan`

5. Execute the below sql

    ```sql
        select count(*) from resource join package on resource.package_id = package.id where package.state = 'active' and resource.state = 'active';
    ```

6. Note down the count of active resources.

## Run the broken links script for a final time

This is so that our "to delete" spreadsheet is as up to date as possible.

1. Execute a shell onto the CKAN pod

2. Dry-run the check links script

    ```bash
        $ python check_links.py --mode dry-run
    ```

<!-- 3. Run the check links script:

    ```bash
        $ python check_links.py --mode live
    ``` -->
    <!-- [TO CONFIRM: does check_links.py delete any records? ] -->

4. Download the report CSV — this becomes the input for the next step.

## Re-run the transient errors workflow

This is to filter out transient errors from the broken links report.

1. Create a local branch in the `datagovuk-scripts` repo

2. Follow the `check-links-analysis/README.md` to filter out transient errors.

3. Use the CSV from the previous step (report CSV)

4. Run the retry once or twice on the report csv. This outputs a retry CSV e.g. `/dd-mm-yyyy/retry_<timestamp>_retry_<timestamp>.csv`

5. Create a pull request in `datagovuk-scripts`, request for a code review then merge to main on approval.

6. Use the retry CSV as the input to the filtering step, below.

## Filter out deferred orgs

1. Create a new branch in `datagovuk-scripts` e.g. `upload-filtered-orgs-report`

2. Go to `datagovuk-scripts/check-links-analysis`

    - Download the broken links csv that we ran all the transient error runs on `/dd-mm-yyyy/retry_<timestamp>_retry_<timestamp>.csv`

3. Run the filter deferred orgs script and provide a list of excluded / deferred orgs e.g. `--exclude org-name=example-org`

    ```bash
        $ scripts/filter.py [broken links csv] [output file path e.g. broken_links_to_delete_20260619T0801.csv] --exclude org-name=abc-agency,def-agency​
    ```

    ⚠️ output file name must be like `broken_links_to_delete_<timestamp>.csv`

    > `<timestamp>` is from check reports github repo

4. Validate that it worked:

- Confirm that the CSV contains less resources and that the excluded orgs aren't in the output csv

## Add the final report to the `datagovuk-scripts` repo

1. After running the above filter script, you should have a CSV written to this path `datagovuk-scripts/check-links-analysis/reports/filtered/<dd-mm-yyyy>/broken_links_to_delete_<timestamp>.csv`

2. Create a pull request and merge to main upon approval.

## Create a PR to add the `checklinks.report` block to `charts/app-of-apps/values-production.yaml`

1. Create a new branch in `govuk-dgu-charts` repo

2. Copy the `checklinks.report` block from `charts/app-of-apps/values-staging.yaml` to  `charts/app-of-apps/values-production.yaml`

    ```yaml
      checklinks:
        report:
            enabled: true
            timestamp: ""
            state: "deleted"
            process_source_url: ""
    ```

3. Set `checklinks.report.timestamp` to the `<timestamp>` from the final filtered CSV in the previous step e.g. `20260626T1022`

4. Set `process_source_url` to the github file location of the filtered out broken links csv from the previous step e.g.
`https://raw.githubusercontent.com/alphagov/datagovuk-scripts/main/check-links-analysis/reports/filtered/<dd-mm-yyyy>/broken_links_to_delete_<timestamp>.csv`

5. Create a pull request, request a review. DO NOT MERGE. Read the next step, below.

## Running the deletion script

1. Communicate to the team channel that you'll be running the deletion script on production

2. Upon approval of the previous step's pull request, merge the PR

3. Switch your local kubernetes context to production like `kubectl config use-context govuk-production`

4. Create the Cron Job manually

    `kubectl create job --from=cronjob/ckan-check-links-process [test-check-links-process-deletion-260626] -n datagovuk`

5. Monitor the cron-job in ARGO in production

## Post live verification

- Verify number of active resources with the same SQL as earlier

    ```sql
    select count(*) from resource join package on resource.package_id = package.id where package.state='active' and resource.state = 'active';
    ```

- Check a sample of records in the database to confirm they have been soft deleted

- After the SOLR index completes, verify on the production site (data.gov.uk) that the resource is no longer being displayed on the dataset/package. Perhaps use a sample of 3 or 4 datasets to verify.
