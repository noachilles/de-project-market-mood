# --- 1단계: Vue.js 프로젝트 빌드 (Builder) ---
FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json ./
COPY package-lock.json ./
RUN npm install

COPY . .

RUN npm run build

# --- 2단계: Nginx 서버 설정 (Server) ---
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html

# nginx.conf 파일을 Nginx 컨테이너에 복사
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]