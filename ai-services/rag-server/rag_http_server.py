import json
import os
from http.server import (
    BaseHTTPRequestHandler,
    ThreadingHTTPServer
)
from urllib.parse import urlparse

from rag_pipeline import (
    answer_question,
    refresh_corpus,
    retrieve_context
)


class RAGHandler(
    BaseHTTPRequestHandler
):

    def _send_json(
        self,
        status_code,
        payload
    ):

        response = json.dumps(
            payload
        ).encode("utf-8")

        self.send_response(
            status_code
        )

        self.send_header(
            "Content-Type",
            "application/json"
        )

        self.send_header(
            "Content-Length",
            str(len(response))
        )

        self.send_header(
            "Access-Control-Allow-Origin",
            "*"
        )

        self.send_header(
            "Access-Control-Allow-Methods",
            "GET, POST, OPTIONS"
        )

        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type"
        )

        self.end_headers()

        self.wfile.write(
            response
        )

    def _read_json(self):

        content_length = int(
            self.headers.get(
                "Content-Length",
                "0"
            )
        )

        if content_length <= 0:
            return {}

        raw = self.rfile.read(
            content_length
        )

        if not raw:
            return {}

        return json.loads(
            raw.decode("utf-8")
        )

    def _get_path(self):

        return urlparse(
            self.path
        ).path

    def _get_k(self, payload):

        try:

            k = int(
                payload.get(
                    "k",
                    5
                )
            )

        except (
            TypeError,
            ValueError
        ):

            raise ValueError(
                "k must be an integer"
            )

        if k <= 0:
            raise ValueError(
                "k must be greater than 0"
            )

        return k

    def do_OPTIONS(self):

        self.send_response(
            204
        )

        self.send_header(
            "Access-Control-Allow-Origin",
            "*"
        )

        self.send_header(
            "Access-Control-Allow-Methods",
            "GET, POST, OPTIONS"
        )

        self.send_header(
            "Access-Control-Allow-Headers",
            "Content-Type"
        )

        self.end_headers()

    def do_GET(self):

        path = self._get_path()

        # -------------------------------------------------
        # Health
        # -------------------------------------------------

        if path == "/health":

            self._send_json(
                200,
                {
                    "status": "ok",
                    "service": "rag-server"
                }
            )

            return

        self._send_json(
            404,
            {
                "status": "error",
                "error": "not_found",
                "path": path
            }
        )

    def do_POST(self):

        path = self._get_path()

        # -------------------------------------------------
        # Read JSON body
        # -------------------------------------------------

        try:

            payload = self._read_json()

        except Exception as exc:

            self._send_json(
                400,
                {
                    "status": "error",
                    "error": f"invalid_json: {exc}"
                }
            )

            return

        try:

            # -------------------------------------------------
            # Refresh RAG corpus
            # -------------------------------------------------

            if path == "/refresh":

                caller = str(
                    payload.get(
                        "caller",
                        "student"
                    )
                ).strip()

                if not caller:
                    caller = "student"

                result = refresh_corpus(
                    caller=caller
                )

                self._send_json(
                    200
                    if result.get(
                        "status"
                    ) == "success"
                    else 500,
                    result
                )

                return

            # -------------------------------------------------
            # Retrieve context
            # -------------------------------------------------

            if path == "/retrieve":

                query = str(
                    payload.get(
                        "query",
                        ""
                    )
                ).strip()

                if not query:

                    self._send_json(
                        400,
                        {
                            "status": "error",
                            "error": "query is required"
                        }
                    )

                    return

                k = self._get_k(
                    payload
                )

                caller = str(
                    payload.get(
                        "caller",
                        "student"
                    )
                ).strip()

                if not caller:
                    caller = "student"

                result = retrieve_context(
                    query=query,
                    k=k,
                    caller=caller
                )

                self._send_json(
                    200
                    if result.get(
                        "status"
                    ) == "success"
                    else 500,
                    result
                )

                return

            # -------------------------------------------------
            # Answer question using RAG
            # -------------------------------------------------

            if path == "/answer":

                query = str(
                    payload.get(
                        "query",
                        ""
                    )
                ).strip()

                if not query:

                    self._send_json(
                        400,
                        {
                            "status": "error",
                            "error": "query is required"
                        }
                    )

                    return

                k = self._get_k(
                    payload
                )

                caller = str(
                    payload.get(
                        "caller",
                        "student"
                    )
                ).strip()

                if not caller:
                    caller = "student"

                result = answer_question(
                    query=query,
                    k=k,
                    caller=caller
                )

                self._send_json(
                    200
                    if result.get(
                        "status"
                    ) == "success"
                    else 500,
                    result
                )

                return

            # -------------------------------------------------
            # Unknown endpoint
            # -------------------------------------------------

            self._send_json(
                404,
                {
                    "status": "error",
                    "error": "not_found",
                    "path": path
                }
            )

        except ValueError as exc:

            self._send_json(
                400,
                {
                    "status": "error",
                    "error": str(exc)
                }
            )

        except Exception as exc:

            self._send_json(
                500,
                {
                    "status": "error",
                    "error": str(exc)
                }
            )


def main():

    host = os.getenv(
        "HOST",
        "0.0.0.0"
    )

    port = int(
        os.getenv(
            "PORT",
            "5003"
        )
    )

    server = ThreadingHTTPServer(
        (
            host,
            port
        ),
        RAGHandler
    )

    print(
        f"RAG HTTP server running "
        f"on {host}:{port}"
    )

    print(
        "Endpoints:"
    )

    print(
        "  GET  /health"
    )

    print(
        "  POST /refresh"
    )

    print(
        "  POST /retrieve"
    )

    print(
        "  POST /answer"
    )

    server.serve_forever()


if __name__ == "__main__":
    main()