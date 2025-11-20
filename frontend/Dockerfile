FROM node:18-alpine
WORKDIR /build
COPY ./package.json ./build/package.json

RUN npm cache clean --force && npm install
