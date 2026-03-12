FROM node:22-alpine

WORKDIR /app

COPY package.json /app/package.json
COPY tsconfig.json /app/tsconfig.json
COPY next-env.d.ts /app/next-env.d.ts
COPY next.config.ts /app/next.config.ts
COPY app /app/app
COPY components /app/components
COPY lib /app/lib

RUN npm install

EXPOSE 3000

CMD ["npm", "run", "dev"]
