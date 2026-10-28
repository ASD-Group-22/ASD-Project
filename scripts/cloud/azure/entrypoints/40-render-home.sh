#!/bin/sh
set -eu

: "${STUDENT1_FRONTEND_URL:?STUDENT1_FRONTEND_URL is required}"
: "${STUDENT2_FRONTEND_URL:?STUDENT2_FRONTEND_URL is required}"
: "${STUDENT3_FRONTEND_URL:?STUDENT3_FRONTEND_URL is required}"
: "${STUDENT4_FRONTEND_URL:?STUDENT4_FRONTEND_URL is required}"
: "${STUDENT5_FRONTEND_URL:?STUDENT5_FRONTEND_URL is required}"

escape_sed() {
    printf '%s' "$1" | sed 's/[&|]/\\&/g'
}

s1="$(escape_sed "$STUDENT1_FRONTEND_URL")"
s2="$(escape_sed "$STUDENT2_FRONTEND_URL")"
s3="$(escape_sed "$STUDENT3_FRONTEND_URL")"
s4="$(escape_sed "$STUDENT4_FRONTEND_URL")"
s5="$(escape_sed "$STUDENT5_FRONTEND_URL")"

sed -i \
    -e "s|__STUDENT1_FRONTEND_URL__|${s1}|g" \
    -e "s|__STUDENT2_FRONTEND_URL__|${s2}|g" \
    -e "s|__STUDENT3_FRONTEND_URL__|${s3}|g" \
    -e "s|__STUDENT4_FRONTEND_URL__|${s4}|g" \
    -e "s|__STUDENT5_FRONTEND_URL__|${s5}|g" \
    /usr/share/nginx/html/index.html
