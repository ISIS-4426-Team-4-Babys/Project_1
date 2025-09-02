FROM postgres:17-alpine

RUN apk update && apk add --no-cache ca-certificates && rm -rf /var/cache/apk/*

COPY init-postgres.sql /docker-entrypoint-initdb.d/init-postgres.sql

RUN chmod 644 /docker-entrypoint-initdb.d/init-postgres.sql

HEALTHCHECK --interval=15s --timeout=5s --start-period=60s --retries=3 \
CMD pg_isready -U ${POSTGRES_USER:-postgres} -d ${POSTGRES_DB} || exit 1

EXPOSE 5432
