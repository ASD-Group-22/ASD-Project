find . -maxdepth 3 -type d | sort
.
./.git
./.git/gk
./.git/hooks
./.git/info
./.git/logs
./.git/logs/refs
./.git/objects
./.git/objects/08
./.git/objects/0c
./.git/objects/12
./.git/objects/14
./.git/objects/15
./.git/objects/1a
./.git/objects/1d
./.git/objects/23
./.git/objects/24
./.git/objects/27
./.git/objects/2a
./.git/objects/2c
./.git/objects/39
./.git/objects/3c
./.git/objects/48
./.git/objects/49
./.git/objects/4c
./.git/objects/51
./.git/objects/63
./.git/objects/68
./.git/objects/6d
./.git/objects/6e
./.git/objects/71
./.git/objects/76
./.git/objects/7a
./.git/objects/7c
./.git/objects/7d
./.git/objects/85
./.git/objects/88
./.git/objects/90
./.git/objects/99
./.git/objects/9e
./.git/objects/a8
./.git/objects/ab
./.git/objects/b9
./.git/objects/bd
./.git/objects/be
./.git/objects/c0
./.git/objects/cc
./.git/objects/d4
./.git/objects/d9
./.git/objects/da
./.git/objects/dc
./.git/objects/e5
./.git/objects/e6
./.git/objects/e9
./.git/objects/ed
./.git/objects/f3
./.git/objects/f6
./.git/objects/f9
./.git/objects/info
./.git/objects/pack
./.git/refs
./.git/refs/heads
./.git/refs/remotes
./.git/refs/tags
./.github
./.github/workflows
./shared
./shared/frontend
./student-1
./student-1/backend
./student-1/backend/prompts
./student-1/backend/routes
./student-1/backend/services
./student-1/database
./student-1/frontend
./student-1/frontend/css
./student-1/frontend/templates
./student-2
./student-2/backend-service
./student-2/backend-service/routes
./student-2/backend-service/services
./student-2/backend-service/views
./student-2/database-service
./student-2/database-service/data
./student-2/evidence
./student-2/frontend-service
./student-2/frontend-service/css
./student-2/frontend-service/templates
./student-2/prompts
./student-2/prompts/skill_exchange
./student-2/scripts
./student-3
./student-3/backend-service
./student-3/backend-service/__pycache__
./student-3/backend-service/routes
./student-3/data
./student-3/database-service
./student-3/database-service/__pycache__
./student-3/database-service/data
./student-3/database-service/models
./student-3/database-service/services
./student-3/evidence
./student-3/frontend-service
./student-3/frontend-service/css
./student-3/frontend-service/js
./student-3/frontend-service/templates
./student-3/prompts
./student-3/prompts/group_service
./student-3/tests
./student-4
./student-4/agentic_loop
./student-4/agentic_loop/logs
./student-4/agentic_loop/prompts
./student-4/backend
./student-4/backend/prompts
./student-4/backend/services
./student-4/database
./student-4/database/data
./student-4/frontend
./student-4/frontend/static
./student-4/frontend/templates
./student-5
./student-5/backend
./student-5/backend/logs
./student-5/backend/prompts
./student-5/backend/tests
./student-5/database
./student-5/database/data
./student-5/database/tests
./student-5/frontend
./student-5/frontend/static
./student-5/frontend/templates

~/ASD-Project integration-test *1 > docker compose config --services 
student-1-database-service
student-1-backend-service
student-1-frontend-service
student-2-skill-exchange-database
student-4-database
student-4-backend
student-2-skill-exchange-backend
student-2-skill-exchange-frontend
student-5-database
home-page
student-3-database
student-3-backend
student-3-frontend
student-5-backend
student-5-frontend
student-4-frontend


docker-compose.yml:
services:

  # SHARED
  home-page:
    image: nginx:alpine
    container_name: home-page
    ports:
      - "3000:80"
    volumes:
      - ./shared/frontend/index.html:/usr/share/nginx/html/index.html:ro
    restart: unless-stopped

  # ==========================================================
  # STUDENT 1
  # ==========================================================

  student-1-database-service:
    build:
      context: ./student-1/database
    container_name: student-1-database-service
    ports:
      - "6001:6001"
    volumes:
      - student_1_database_data:/app/data
    restart: unless-stopped


  student-1-backend-service:
    build:
      context: ./student-1/backend
    container_name: student-1-backend-service
    ports:
      - "5001:5001"
    environment:
      DATABASE_SERVICE_URL: "http://student-1-database-service:6001"
      OLLAMA_BASE_URL: "${STUDENT1_OLLAMA_BASE_URL:-http://host.docker.internal:11434}"
      OLLAMA_MODEL: "${OLLAMA_MODEL:-qwen3:8b}"
      OLLAMA_REVIEW_MODEL: "${OLLAMA_REVIEW_MODEL:-llama3.1:8b}"
    depends_on:
      - student-1-database-service
    restart: unless-stopped


  student-1-frontend-service:
    build:
      context: ./student-1/frontend
    container_name: student-1-frontend-service
    ports:
      - "3001:80"
    depends_on:
      - student-1-backend-service
    restart: unless-stopped


  # ==========================================================
  # STUDENT 2
  # ==========================================================

  student-2-skill-exchange-frontend:
    build:
      context: ./student-2/frontend-service
    container_name: student-2-skill-exchange-frontend
    ports:
      - "8202:80"
    depends_on:
      - student-2-skill-exchange-backend
    networks:
      - student-2-network
    restart: unless-stopped


  student-2-skill-exchange-backend:
    build:
      context: ./student-2
      dockerfile: backend-service/Dockerfile
    container_name: student-2-skill-exchange-backend
    ports:
      - "5202:5001"
    environment:
      DATABASE_SERVICE_URL: http://student-2-skill-exchange-database:5002
      OLLAMA_BASE_URL: "${STUDENT2_OLLAMA_BASE_URL:-http://host.docker.internal:11434/v1}"
      OLLAMA_MODEL: "${OLLAMA_MODEL:-qwen3:8b}"
      OLLAMA_REVIEW_MODEL: "${OLLAMA_REVIEW_MODEL:-llama3.1:8b}"
      ENABLE_REVIEW_MODEL: "true"
      SKILL_PROFILE_SERVICE_URL: "http://student-4-backend:5005"
    extra_hosts:
      - "host.docker.internal:host-gateway"
    depends_on:
      - student-2-skill-exchange-database
      - student-4-backend
    networks:
      - student-2-network
    restart: unless-stopped


  student-2-skill-exchange-database:
    build:
      context: ./student-2/database-service
    container_name: student-2-skill-exchange-database
    ports:
      - "5302:5002"
    volumes:
      - student_2_skill_exchange_data:/app/data
    networks:
      - student-2-network
    restart: unless-stopped

  # ==========================================================
  # STUDENT 3
  # ==========================================================

  student-3-database:
    build: ./student-3/database-service
    volumes:
      - ./student-3/database-service/data:/app/data
    ports:
      - "6000:6000"
    restart: unless-stopped

  student-3-backend:
    build: ./student-3/backend-service
    ports:
      - "5000:5000"
    volumes:
      - ./student-3/prompts:/prompts:ro
    environment:
      DB_URL: "http://student-3-database:6000"
      SKILL_PROFILE_SERVICE_URL: "http://student-4-backend:5005"
      OLLAMA_URL: "${STUDENT3_OLLAMA_URL:-http://host.docker.internal:11434}"
      OLLAMA_MODEL: "${STUDENT3_OLLAMA_MODEL:-llama3.1:8b}"
      PROMPT_ROOT: "/prompts"
    extra_hosts:
      - "host.docker.internal:host-gateway"
    depends_on:
      - student-3-database
      - student-4-backend
    restart: unless-stopped

  student-3-frontend:
    build: ./student-3/frontend-service
    ports:
      - "8000:8000"
    depends_on:
      - student-3-backend
    restart: unless-stopped


  # ==========================================================
  # STUDENT 4
  # ==========================================================

  student-4-database:
    build:
      context: ./student-4/database
    container_name: student-4-database
    ports:
      - "5004:5004"
    volumes:
      - student_4_skill_profile_data:/app/data
    restart: unless-stopped

  student-4-backend:
    build:
      context: ./student-4/backend
    container_name: student-4-backend
    ports:
      - "5005:5005"
    environment:
      DATABASE_SERVICE_URL: "http://student-4-database:5004"
      OLLAMA_URL: "http://host.docker.internal:11434"
      OLLAMA_MODEL: "${OLLAMA_MODEL:-qwen3:8b}"
    extra_hosts:
      - "host.docker.internal:host-gateway"
    depends_on:
      - student-4-database
    networks:
      - default
      - student-2-network
    restart: unless-stopped

  student-4-frontend:
    build:
      context: ./student-4/frontend
    container_name: student-4-frontend
    ports:
      - "5006:5006"
    environment:
      BACKEND_SERVICE_URL: "http://student-4-backend:5005"
    depends_on:
      - student-4-backend
    restart: unless-stopped


  # ==========================================================
  # STUDENT 5
  # ==========================================================

  student-5-database:
    build:
      context: ./student-5/database
    container_name: student-5-database
    volumes:
      - student_5_database_data:/data
    restart: unless-stopped


  student-5-backend:
    build:
      context: ./student-5/backend
    container_name: student-5-backend
    ports:
      - "8055:8055"
    environment:
      DATABASE_SERVICE_URL: "http://student-5-database:5000"
      OLLAMA_URL: "http://host.docker.internal:11434"
      OLLAMA_MODEL: "qwen3:8b"
    extra_hosts:
      - "host.docker.internal:host-gateway"
    depends_on:
      - student-5-database
    restart: unless-stopped


  student-5-frontend:
    build:
      context: ./student-5/frontend
    container_name: student-5-frontend
    ports:
      - "8005:8005"
    environment:
      BACKEND_PUBLIC_URL: "http://localhost:8055"
    depends_on:
      - student-5-backend
    restart: unless-stopped

volumes:
  student_1_database_data:
  student_2_skill_exchange_data:
  student_4_skill_profile_data:
  student_5_database_data:

networks:
  default:
    driver: bridge
  student-2-network:
    driver: bridge


docker compose config --services
student-4-database
student-4-backend
student-4-frontend
student-5-database
student-5-backend
student-5-frontend
student-1-database-service
student-1-backend-service
student-1-frontend-service
student-3-database
student-3-backend
student-3-frontend
home-page
student-2-skill-exchange-database
student-2-skill-exchange-backend
student-2-skill-exchange-frontend


~/ASD-Project integration-test *1 !1 > docker compose ps                                                               3s 02:35:36 PM
NAME                                IMAGE                                           COMMAND                  SERVICE           CREATED         STATUS         PORTS
asd-project-student-3-backend-1     asd-project-student-3-backend                   "python app.py"          student-3-backend           3 minutes ago   Up 3 minutes   0.0.0.0:5000->5000/tcp, [::]:5000->5000/tcp
asd-project-student-3-database-1    asd-project-student-3-database                  "sh -c 'python init_…"   student-3-database           3 minutes ago   Up 3 minutes   0.0.0.0:6000->6000/tcp, [::]:6000->6000/tcp
asd-project-student-3-frontend-1    asd-project-student-3-frontend                  "python -m http.serv…"   student-3-frontend           3 minutes ago   Up 3 minutes   0.0.0.0:8000->8000/tcp, [::]:8000->8000/tcp
home-page                           nginx:alpine                                    "/docker-entrypoint.…"   home-page           3 minutes ago   Up 3 minutes   0.0.0.0:3000->80/tcp, [::]:3000->80/tcp
student-1-backend-service           asd-project-student-1-backend-service           "python app.py"          student-1-backend-service           3 minutes ago   Up 3 minutes   0.0.0.0:5001->5001/tcp, [::]:5001->5001/tcp
student-1-database-service          asd-project-student-1-database-service          "sh -c 'python init_…"   student-1-database-service          3 minutes ago   Up 3 minutes   0.0.0.0:6001->6001/tcp, [::]:6001->6001/tcp
student-1-frontend-service          asd-project-student-1-frontend-service          "/docker-entrypoint.…"   student-1-frontend-service          3 minutes ago   Up 3 minutes   0.0.0.0:3001->80/tcp, [::]:3001->80/tcp
student-2-skill-exchange-backend    asd-project-student-2-skill-exchange-backend    "python backend-serv…"   student-2-skill-exchange-backend    3 minutes ago   Up 3 minutes   0.0.0.0:5202->5001/tcp, [::]:5202->5001/tcp
student-2-skill-exchange-database   asd-project-student-2-skill-exchange-database   "sh -c 'python init_…"   student-2-skill-exchange-database   3 minutes ago   Up 3 minutes   0.0.0.0:5302->5002/tcp, [::]:5302->5002/tcp
student-2-skill-exchange-frontend   asd-project-student-2-skill-exchange-frontend   "/docker-entrypoint.…"   student-2-skill-exchange-frontend   3 minutes ago   Up 3 minutes   0.0.0.0:8202->80/tcp, [::]:8202->80/tcp
student-4-backend                   asd-project-student-4-backend                   "python app.py"          student-4-backend           3 minutes ago   Up 3 minutes   0.0.0.0:5005->5005/tcp, [::]:5005->5005/tcp
student-4-database                  asd-project-student-4-database                  "sh -c 'python init_…"   student-4-database           3 minutes ago   Up 3 minutes   0.0.0.0:5004->5004/tcp, [::]:5004->5004/tcp
student-4-frontend                  asd-project-student-4-frontend                  "python app.py"          student-4-frontend           3 minutes ago   Up 3 minutes   0.0.0.0:5006->5006/tcp, [::]:5006->5006/tcp
student-5-backend                   asd-project-student-5-backend                   "python app.py"          student-5-backend           3 minutes ago   Up 3 minutes   0.0.0.0:8055->8055/tcp, [::]:8055->8055/tcp
student-5-database                  asd-project-student-5-database                  "python app.py"          student-5-database           3 minutes ago   Up 3 minutes   5000/tcp
student-5-frontend                  asd-project-student-5-frontend                  "python app.py"          student-5-frontend           3 minutes ago   Up 3 minutes   0.0.0.0:8005->8005/tcp, [::]:8005->8005/tcp



~/ASD-Project integration-test *1 !1 > ls -la .github/workflows                                                           02:35:55 PM
total 32
drwxr-xr-x  9 maen03  staff   288 Sep  7 14:20 .
drwxr-xr-x  3 maen03  staff    96 Aug 26 16:48 ..
-rw-r--r--  1 maen03  staff     0 Aug 26 16:48 cloud-deployment.yml
-rw-r--r--  1 maen03  staff     0 Aug 26 16:48 integration-ci.yml
-rw-r--r--  1 maen03  staff     0 Aug 26 16:48 student-1-ci.yml
-rw-r--r--  1 maen03  staff  4758 Sep  3 23:48 student-2-ci.yml
-rw-r--r--  1 maen03  staff  3002 Sep  7 14:20 student-3-ci.yml
-rw-r--r--  1 maen03  staff  3801 Sep  7 14:20 student-4-ci.yml
-rw-r--r--  1 maen03  staff     0 Sep  3 23:48 student-5-ci.yml