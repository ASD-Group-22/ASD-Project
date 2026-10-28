FROM nginx:alpine

COPY student-2/frontend-service/templates/ /usr/share/nginx/html/
COPY student-2/frontend-service/css/ /usr/share/nginx/html/css/
COPY student-2/frontend-service/js/ /usr/share/nginx/html/js/

COPY scripts/cloud/azure/nginx/backend-proxy.conf.template \
     /etc/nginx/templates/default.conf.template

# MCP, RAG and Multi-Agent already use /api.
# Normal and AI Mode use localhost locally, so convert them only in this
# cloud-specific image.
RUN sed -i \
    "s|const API = .*;|const API = '/api';|" \
    /usr/share/nginx/html/tabs/normal.html \
    /usr/share/nginx/html/tabs/ai-mode.html

EXPOSE 80
