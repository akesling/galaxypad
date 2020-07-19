FROM icfpcontest2020/python

WORKDIR /solution
COPY . .
RUN chmod +x ./build.sh
RUN chmod +x ./run.sh
RUN ./build.sh

RUN pip install -r ui/requirements.txt

WORKDIR /solution/ui/frontend
RUN apt-get install curl && \
    curl -sL https://deb.nodesource.com/setup_12.x | bash - && \
    apt-get install nodejs && \
    npm install && \
    npm run build

WORKDIR /solution/ui