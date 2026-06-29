# Playbook for soft deleting broken resource links

1. Count active resources
2. Filter out deferred orgs
3. Upload to S3
4. Run the deletion and SOLR reindex script

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

## Filter out deferred orgs

> *prerequisites:*
>
> ⚠️ Use the verified broken links CSV from the Transient errors script.

1. Go to `datagovuk-scripts/check-links-transient`

    - Use the broken links csv that we ran all the transient error runs on

    - Filter out organisations that have opted out

1. Run the filter deferred orgs script

    ```bash
    $ scripts/filter.py [broken links csv] [output file path e.g. broken_links_to_delete_20260619T0801.csv] --exclude abc-agency,def-agency​
    ```

⚠️ output file name must be like `broken_links_to_delete_$TIMESTAMP.csv`

$TIMESTAMP is from check reports github repo 

1. Conirm the count of filtered orgs match 

2. Upload the filtered out broken links csv ( `broken_links_to_delete_$TIMESTAMP.csv` ) to the S3 ckan-output bucket 

    (It failed, so we uploaded it manually to a pod)
Blocker ⚠️

    [ ] We need to be able to upload files to S3

    *Workaround:*

    [ ]  In govuk-dgu-charts repo under check_links-process.sh in the yaml cronjob template ckan/templates/cronjobs/check-links-process-script.yaml, comment out the deletion script run (process_check_links_report.py).

    Also, comment out the solr reindex python script call.

    This is to upload to S3 and then run the commented out scripts manually
    Deletion Process

## Running the deletion + reindex script

1. Create PR to update checklinks.report.timestamp in `values-[env].yml` in `govuk-dgu-charts` to the timestamp of the file e.g. `20260619T0801`

2. Communicate actions to the team channel

3. Merge PR

4. Run the Cron Job manually

    `kubectl create job --from=cronjob/ckan-check-links-process [test-check-links-process-deletion-260626] -n datagovuk`

    ⚠️ Because of the workaround for s3 access we manually copied the file onto the pod after step 4.

5. Exec onto the cronjob ckan pod

6. Run the script

7. Sanity check the number of resources that will be deleted

8. Monitor the cron-job in ARGO

## Post live verification

- Check a sample of records in the database to confirm they have been soft deleted

- After the SOLR index completes, verify on the [environent].data.gov.uk that the resource is no longer being displayed on the dataset/package
