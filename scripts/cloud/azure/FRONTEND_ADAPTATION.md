# Cloud Frontend Adaptation Plan

## Shared Home

Current local behaviour:
- Links to localhost ports 3001, 8202, 8000, 5006 and 8005.
- Local JavaScript can rewrite the hostname while retaining local ports.

Azure requirement:
- Inject the five real external Student frontend URLs.
- Do not rely on same-host port rewriting because each Azure Container App has
  its own FQDN.

Recommended implementation:
- Cloud-specific static template or build-time URL replacement.

## Student 1

Current implementation:
- Static Nginx frontend.
- Normal feature pages use API_URL / BACKEND_URL variables.
- MCP pages contain direct localhost:5001 HTMX targets.

Azure requirement:
- Browser must not call the internal backend FQDN directly.

Recommended implementation:
- Cloud-specific Nginx configuration.
- Convert backend requests to same-origin /api paths.
- Nginx proxies /api to the Student 1 internal backend FQDN.

Exact source replacements should be verified before implementation.

## Student 2

Current implementation:
- Static Nginx frontend.
- MCP, RAG and Multi-Agent already use /api.
- Normal and AI pages require cloud adaptation.

Proven Student 2 POC implementation:
- Cloud image replaces remaining backend URLs with /api.
- Nginx runtime template receives BACKEND_ORIGIN.
- /api is reverse-proxied to the Student 2 internal backend.
- HTTPS SNI configuration has already been tested successfully in Azure.

This should remain the reference pattern for static frontends.

## Student 3

Current implementation:
- Static files served through python -m http.server.
- Browser computes backend URL using the current hostname and local port 5009.
- UI contains a localhost:5006 link to the Student 4 frontend.

Azure requirement:
- Student 3 backend remains internal.
- Student 4 frontend has a separate external FQDN.

Recommended implementation:
- Use a cloud-specific Nginx image for the static Student 3 frontend.
- Convert Student 3 backend requests to same-origin /api.
- Nginx proxies /api to Student 3 internal backend.
- Inject the external Student 4 frontend URL into the cloud frontend.

## Student 4

Current implementation:
- Python/Flask frontend.
- Backend address comes from BACKEND_SERVICE_URL.
- Backend requests are performed server-side.

Azure requirement:
- Set BACKEND_SERVICE_URL to the Student 4 internal backend ACA FQDN.

This frontend requires the least cloud-specific adaptation.

## Student 5

Current implementation:
- Python frontend renders BACKEND_PUBLIC_URL into browser JavaScript.
- Browser JavaScript then calls the backend directly.

Problem:
- An internal ACA backend cannot be reached directly from the public user's
  browser.

Recommended implementation:
- Keep Student 5 backend internal.
- Add same-origin proxy routes to the Student 5 frontend, or provide a
  cloud-specific frontend adapter that proxies requests server-side.
- Browser JavaScript should use relative frontend URLs rather than the internal
  backend FQDN.

Making Student 5 backend publicly accessible should be treated as a fallback,
not the preferred architecture.

## Overall Rule

Preferred cloud request path:

    Browser
      -> External frontend Container App
      -> Same-origin /api or server-side request
      -> Internal backend Container App
      -> Internal database Container App

Cross-feature backend requests remain server-to-server within the Container
Apps environment.

## Excluded VM-Era Routing Experiments

The current private working tree contains earlier experimental changes that
replace localhost with the browser's current hostname while retaining local
host ports, for example:

    current-host:5001
    current-host:5202
    current-host:5009

Similar hostname rewriting also exists experimentally in the shared home page.

These changes were designed for a single-host/VM deployment and are not the
target Azure Container Apps architecture.

They must not be used as the final ACA routing solution because each externally
accessible Container App receives its own FQDN and the backend Container Apps
are intended to remain internal.

The final ACA implementation should instead use:

- same-origin frontend proxy routes such as /api;
- server-side frontend-to-backend requests where appropriate; and
- explicit external frontend FQDN injection for cross-feature navigation.
