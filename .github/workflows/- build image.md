- build image
- run tests?
- run security checks? make sure there aren't any secrets being released

- after success it creates a PR in the helm charts repo?

------

Seems like i need to first create a place in the helms chart repo for it


----

What do i need the docke rimage to do?

i need these packages: requests,boto3 (for s3), psycopg2 (postgres database calls), pytest

i need it a local setup and a whole suite setup:
- local contains a mock db and mock ckan?
- whole suite is ckan,postgres setup that exists in ckanext-datagovuk