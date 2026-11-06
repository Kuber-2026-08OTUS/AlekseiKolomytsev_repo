FROM python:3.11-slim
RUN pip install kopf kubernetes
COPY handlers.py /src/handlers.py
CMD ["kopf", "run", "/src/handlers.py", "--verbose"]
