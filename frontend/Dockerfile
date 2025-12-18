FROM node:18-alpine
WORKDIR /build
COPY package.json package-lock.json ./
RUN npm install

COPY ./ /build
RUN npm run build
EXPOSE 8080
CMD ["npm", "start"]
