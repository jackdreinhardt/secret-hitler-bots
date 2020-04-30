FROM python:3 as build

RUN pip install pipenv
COPY Pipfile* /tmp/
RUN cd /tmp && pipenv lock --requirements > requirements.txt
RUN pip install -r /tmp/requirements.txt && cd /

FROM build

ADD agents agents
ADD battlefield battlefield
ADD models models
ADD secrethitler secrethitler
ADD run_sh_game.py .

ENTRYPOINT ["python", "-O", "./run_sh_game.py"]