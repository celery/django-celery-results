FROM python:3.13.3-slim AS base

LABEL authors='Diego Castro <diego.castro@kubicum.com>' \
    org.opencontainers.image.description='A Docker image to run tests for Django Celery Results using Tox' \
    org.opencontainers.image.documentation='https://django-celery-results.readthedocs.io/' \
    org.opencontainers.image.license='BSD-3-Clause' \
    org.opencontainers.image.source='https://github.com/celery/django-celery-results' \
    org.opencontainers.image.title='Dockerized Tox suite for Django Celery Results' \
    org.opencontainers.image.vendor='Celery'

RUN <<EOF
    apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        wget \
        gnupg \
        zlib1g-dev \
        libbz2-dev \
        libreadline-dev \
        libsqlite3-dev \
        libssl-dev \
        libffi-dev \
        libpq-dev \
        postgresql-client \
        xz-utils \
        tk-dev \
        libncurses5-dev \
        git \
        bash && \
        apt-get clean && rm -rf /var/lib/apt/lists/*
EOF

ENV PYTHON_VERSIONS="3.12.3 3.11.9 3.10.14 3.9.19 3.8.20" \
    PYPY_VERSION="pypy3.10-v7.3.19-linux64"

RUN <<EOF
    for version in $PYTHON_VERSIONS; do
        VERSION_MAJOR_MINOR=$(echo $version | cut -d. -f1-2) &&

        wget https://www.python.org/ftp/python/${version}/Python-${version}.tgz &&
        tar -xzf Python-${version}.tgz && cd Python-${version} &&

        ./configure \
            --prefix=/usr \
            --enable-optimizations \
            --with-ensurepip=install \
            --enable-shared &&

        make -j$(nproc) && make altinstall &&
        cd .. && rm -rf Python-${version} Python-${version}.tgz &&

        ln -sf /usr/bin/python${VERSION_MAJOR_MINOR} /usr/bin/python${VERSION_MAJOR_MINOR%.*}
    done
EOF

RUN <<EOF
    wget https://downloads.python.org/pypy/${PYPY_VERSION}.tar.bz2 &&
    mkdir -p /opt/pypy310 &&
    tar -xjC /opt/pypy310 --strip-components=1 -f ${PYPY_VERSION}.tar.bz2 &&
    find /opt/pypy310/lib* -depth -type d -a \( -name test -o -name tests \) -exec rm -rf '{}' +;

    rm ${PYPY_VERSION}.tar.bz2 &&

    ln -sf /opt/pypy310/bin/pypy3 /usr/bin/
    ln -sf /opt/pypy310/bin/pypy3 /usr/bin/pypy3.10
EOF

RUN pip install --upgrade pip && pip install --no-cache-dir tox

WORKDIR /usr/src/celery/django-celery-results

COPY . .

ENTRYPOINT ["tox"]
