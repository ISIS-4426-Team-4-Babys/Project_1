# Use official lightweight PostgreSQL Alpine image
FROM postgres:17-alpine

# Install security-related packages (e.g. CA certificates)
RUN apk update && apk add --no-cache ca-certificates && rm -rf /var/cache/apk/*

# Copy database initialization SQL script to entrypoint folder
COPY init-postgres.sql /docker-entrypoint-initdb.d/init-postgres.sql

# Set read permissions for the initialization script
RUN chmod 644 /docker-entrypoint-initdb.d/init-postgres.sql

# Health check to verify DB readiness every 15 seconds
# Waits 60 seconds before starting checks; fails after 3 unsuccessful tries
HEALTHCHECK --interval=15s --timeout=5s --start-period=60s --retries=3 \
CMD pg_isready -U ${POSTGRES_USER:-postgres} -d todo-db || exit 1

# Port 5432 is exposed by default and container runs as postgres user
EXPOSE 5432