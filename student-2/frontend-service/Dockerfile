FROM nginx:alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf

COPY templates/ /usr/share/nginx/html/
COPY css/ /usr/share/nginx/html/css/
COPY js/ /usr/share/nginx/html/js/

EXPOSE 80
