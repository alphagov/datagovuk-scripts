FROM ghcr.io/alphagov/ckan:2.10.7-d

ENV APP_PATH=/app

WORKDIR ${APP_PATH}

COPY ./remove_duplicate_datasets.py ${APP_PATH}/remove_duplicate_datasets.py
COPY ./requirements.txt ${APP_PATH}/requirements.txt

RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH=${APP_PATH}
