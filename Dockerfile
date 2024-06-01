FROM python:3.11

WORKDIR /app

COPY . /app

RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y

ENV PATH="/root/.cargo/bin:${PATH}"

RUN pip install --no-cache-dir -r requirements.txt

RUN pip install uvicorn[standard]

RUN pip install pip install tortoise-orm[asyncmy]

RUN pip install pyppeteer-install

RUN apt-get update && apt-get install -y wget xvfb libxss1 libappindicator1

RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN dpkg -i google-chrome-stable_current_amd64.deb; apt-get -fy install

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8900"]

EXPOSE 8900
