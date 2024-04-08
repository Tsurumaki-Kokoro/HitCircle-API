FROM python:3.11

WORKDIR /app

COPY . /app

RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y

ENV PATH="/root/.cargo/bin:${PATH}"

RUN pip install --no-cache-dir -r requirements.txt

RUN pip install uvicorn[standard]

RUN pip install pip install tortoise-orm[asyncmy]

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8900"]

EXPOSE 8900
