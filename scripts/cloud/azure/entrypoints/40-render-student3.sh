#!/bin/sh
set -eu

if [ -z "${STUDENT4_FRONTEND_URL:-}" ]; then
    echo "ERROR: STUDENT4_FRONTEND_URL is required." >&2
    exit 1
fi

escaped_url="$(printf '%s' "$STUDENT4_FRONTEND_URL" | sed 's/[&|]/\\&/g')"

sed -i \
    "s|__STUDENT4_FRONTEND_URL__|${escaped_url}|g" \
    /usr/share/nginx/html/index.html
