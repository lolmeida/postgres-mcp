#!/bin/bash


# Run docker postgres db
docker run --name postgres-mcp -e POSTGRES_PASSWORD=postgres -e POSTGRES_USER=postgres -e POSTGRES_DB=postgres -p 5432:5432 -d postgres:15
