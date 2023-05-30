FROM hashicorp/terraform:latest as terraform 

# Use an official Python runtime as a parent image
FROM python:3.9-slim-buster AS py

# Set the working directory to /cli
WORKDIR /cli

COPY --from=terraform /bin/terraform /bin/terraform

# Copy the poetry.lock and pyproject.toml files to the container
COPY poetry.lock pyproject.toml VERSION /cli/

RUN apt-get update && apt-get install curl gnupg -y

RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - && \
    curl https://packages.microsoft.com/config/debian/10/prod.list > /etc/apt/sources.list.d/mssql-release.list && \
    apt-get update && \ 
    ACCEPT_EULA=Y apt-get install -y msodbcsql17 unixodbc-dev

# Install Poetry
RUN pip install poetry 

# update poetry
RUN poetry self update

# Install the application dependencies using Poetry
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --only main


# Copy the application code to the container
COPY cloudforge/ /cli/cloudforge

RUN poetry build --no-ansi

RUN pip install dist/*.whl

COPY docker-entrypoint.sh /cli/docker-entrypoint.sh

# Set the entrypoint to run the application with Poetry
ENTRYPOINT ["/cli/docker-entrypoint.sh"]

