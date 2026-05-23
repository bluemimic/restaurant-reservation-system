# restaurant-reservation-system
A small Django-based reservation system (OOP assignment).

Quick start — Docker
- Requirements: Docker (and Docker Compose v2).
- Build & run (foreground):
  docker compose -f docker-compose.dev.yaml up --build
- Run detached:
  docker compose -f docker-compose.dev.yaml up -d --build
- View logs:
  docker compose -f docker-compose.dev.yaml logs -f
- Stop and remove containers:
  docker compose -f docker-compose.dev.yaml down

Running management commands
- Migrate:
  docker compose exec web python manage.py migrate
- Shell / createsuperuser:
  docker compose exec web python manage.py shell
  docker compose exec web python manage.py createsuperuser

Debugging with VS Code (Python)
1) Ensure the Python extension is installed.
2) Add debugpy to your container (in requirements) or install inside container.
3) Start Django with debugpy listening (example):
   docker compose exec web python -m debugpy --listen 0.0.0.0:5678 --wait-for-client manage.py runserver 0.0.0.0:8000
   - --wait-for-client blocks until VS Code attaches (useful for initial breakpoints).

Example .vscode/launch.json snippet (attach):
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Attach to Django in Docker",
      "type": "python",
      "request": "attach",
      "connect": { "host": "localhost", "port": 5678 },
      "pathMappings": [ { "localRoot": "${workspaceFolder}", "remoteRoot": "/app" } ]
    }
  ]
}

Notes & tips
- remoteRoot must match the container WORKDIR (check Dockerfile). Adjust "/app" if different.
- Use --wait-for-client to ensure early breakpoints are hit.
- To run a one-off debug command:
  docker compose exec web python -m debugpy --listen 0.0.0.0:5678 manage.py shell
- Use docker compose exec web /bin/sh to open an interactive shell inside the container.
- Keep sensible .env files out of source control; copy .env.example to .env locally.

Troubleshooting
- If VS Code cannot attach, verify container exposes the debug port and firewall allows localhost loopback.
- If breakpoints are ignored, fix pathMappings so local paths map to container paths.

Contact
- For more environment-specific tips, describe your OS and Docker setup when asking for help.
