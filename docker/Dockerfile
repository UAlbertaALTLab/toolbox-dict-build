FROM python:3.10-slim-bookworm
LABEL maintainer="Felipe Bañados Schwerter <banadoss@ualberta.ca>"
RUN apt-get update \
    && apt-get install -y texlive texlive-xetex wget unzip default-jre
RUN pip install pipenv
ARG UID_GID=60005
ARG WSGI_USER=arok
# Create the user/group for the application
RUN groupadd --system --gid ${UID_GID} ${WSGI_USER} \
 && useradd --no-log-init --system --gid ${WSGI_USER} --uid ${UID_GID} ${WSGI_USER} \
 && mkdir /app \
 && chown ${WSGI_USER}:${WSGI_USER} /app

USER ${WSGI_USER}:${WSGI_USER}
WORKDIR /app/
ENV VIRTUAL_ENV="/app/.venv"
ENV PATH="${VIRTUAL_ENV}/bin:${PATH}"
ENV PYTHONPATH="/app/src"
EXPOSE 8000

# Now we'll get the stanford corenlp tools
RUN wget https://nlp.stanford.edu/software/stanford-corenlp-4.5.9.zip
RUN unzip stanford-corenlp-4.5.9.zip
ENV CLASSPATH="/app/stanford-corenlp-4.5.9"
ADD Pipfile Pipfile.lock ./
RUN PIPENV_VENV_IN_PROJECT=1 pipenv install --deploy

ADD src/ /app/
#CMD ["tail", "-f", "/dev/null"]
CMD [ "./app.sh" ]
#CMD "ls .; echo \"ASDF\"; /app/.venv/bin/python ./server.py"