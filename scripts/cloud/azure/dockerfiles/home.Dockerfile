FROM nginx:alpine

COPY shared/frontend/index.html /usr/share/nginx/html/index.html

COPY scripts/cloud/azure/entrypoints/40-render-home.sh \
     /docker-entrypoint.d/40-render-home.sh

RUN chmod +x /docker-entrypoint.d/40-render-home.sh \
    && sed -i \
       -e 's|http://localhost:3001|__STUDENT1_FRONTEND_URL__|g' \
       -e 's|http://localhost:8202|__STUDENT2_FRONTEND_URL__|g' \
       -e 's|http://localhost:8000|__STUDENT3_FRONTEND_URL__|g' \
       -e 's|http://localhost:5006|__STUDENT4_FRONTEND_URL__|g' \
       -e 's|http://localhost:8005|__STUDENT5_FRONTEND_URL__|g' \
       /usr/share/nginx/html/index.html

EXPOSE 80
