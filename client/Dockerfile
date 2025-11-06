FROM node:latest as build-stage
WORKDIR /front
COPY package*.json ./
RUN npm install
COPY ../front .
RUN npm run build

FROM nginx as production-stage
COPY certs/ /certs/
RUN mkdir /front
COPY --from=build-stage /front/dist /front
COPY nginx.conf /etc/nginx/nginx.conf
