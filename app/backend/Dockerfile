FROM python:3.11-bullseye

# Instalează driver-ele Microsoft ODBC pentru SQL Server
RUN apt-get update && apt-get install -y \
    curl \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release

# Adaugă cheia Microsoft și repository-ul pentru ODBC Driver
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list

# Instalează Microsoft ODBC Driver pentru SQL Server
RUN apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
    && apt-get install -y unixodbc-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY ./ /app

RUN python -m pip install -r requirements.txt

RUN python -m pip install gunicorn

CMD ["python3", "-m", "gunicorn", "-b", "0.0.0.0:8000", "main:app"]
