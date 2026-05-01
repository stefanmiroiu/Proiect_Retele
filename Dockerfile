# Folosim o imagine de baza oficiala si usoara de Python
FROM python:3.9-slim

# Ne setam directorul de lucru in interiorul containerului
WORKDIR /app

# Copiem toate fisierele noastre (.py) in container
COPY . /app/

