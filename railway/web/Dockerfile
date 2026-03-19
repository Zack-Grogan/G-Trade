FROM node:20-slim
WORKDIR /app
COPY package.json bun.lock ./
RUN npm install --ignore-scripts
COPY . .
RUN npm run build && mkdir -p .next/standalone/.next && cp -r .next/static .next/standalone/.next/ && if [ -d public ]; then cp -r public .next/standalone/; fi
EXPOSE 8080
ENV PORT=8080
ENV HOSTNAME=0.0.0.0
ENV NODE_ENV=production
CMD ["node", ".next/standalone/server.js"]
