FROM ghcr.io/alphagov/ckan:2.10.7-b

ENV APP_PATH=/app/check-links

WORKDIR ${APP_PATH}

COPY ./lib/s3.py ${APP_PATH}/lib/s3.py
COPY ./check_links.py ${APP_PATH}/check_links.py
COPY ./process_check_links_report.py ${APP_PATH}/process_check_links_report.py
COPY ./requirements.txt ${APP_PATH}/requirements.txt

RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONPATH=${APP_PATH}
