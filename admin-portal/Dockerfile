# Stage 0, "build-stage", based on Node.js, to build and compile the frontend
FROM node:24

WORKDIR /app

COPY package.json .

RUN npm install

RUN npm i -g serve

COPY . .

RUN npm run build

EXPOSE 8080

CMD ["sh", "-c", "serve -s dist -l ${PORT:-8080}"]