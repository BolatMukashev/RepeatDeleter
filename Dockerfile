FROM python:3

WORKDIR /python

COPY requirements.txt /python
RUN pip install --no-cache-dir -r requirements.txt

COPY . /python

CMD [ "python", "./RepeatDeleter.py" ]