FROM python:3.13-alpine
WORKDIR /build
COPY ./requirements.txt /build/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /build/requirements.txt
COPY ./ /build
CMD ["fastapi", "run", "/build/main.py", "--port", "8000"]