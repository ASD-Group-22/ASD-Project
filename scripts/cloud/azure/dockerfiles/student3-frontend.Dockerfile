FROM nginx:alpine

COPY student-3/frontend-service/ /usr/share/nginx/html/

COPY scripts/cloud/azure/nginx/backend-proxy.conf.template \
     /etc/nginx/templates/default.conf.template

COPY scripts/cloud/azure/entrypoints/40-render-student3.sh \
     /docker-entrypoint.d/40-render-student3.sh

RUN chmod +x /docker-entrypoint.d/40-render-student3.sh \
    && sed -i \
       "s|const backend = \"http://localhost:5009\";|const backend = '/api';|" \
       /usr/share/nginx/html/index.html \
    && sed -i \
       "s|http://localhost:5006|__STUDENT4_FRONTEND_URL__|g" \
       /usr/share/nginx/html/index.html

EXPOSE 80
