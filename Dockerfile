FROM obolibrary/odkfull

COPY requirements.txt /tools/ihcc-requirements.txt
RUN pip install -r /tools/ihcc-requirements.txt

RUN apt-get install aha dos2unix sqlite3
