FROM nginx:alpine

COPY student-1/frontend/templates/ /usr/share/nginx/html/
COPY student-1/frontend/css/ /usr/share/nginx/html/css/

COPY scripts/cloud/azure/nginx/backend-proxy.conf.template \
     /etc/nginx/templates/default.conf.template

# Local Student 1 pages address the backend through localhost:5001.
# In ACA, browser requests go through this frontend's /api reverse proxy.
RUN find /usr/share/nginx/html \
    -type f \
    -name "*.html" \
    -exec sed -i 's|http://localhost:5001|/api|g' {} +

EXPOSE 80
