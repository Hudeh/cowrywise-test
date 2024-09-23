# Library Management Api

Library Management and Infrastructure Deployment

## Getting Started

### Prerequisites

- Python 3.x
- Docker
- Docker Compose
- RabbitMQ
- PostgreSQL

### Installation

1. **Clone the repository:**

    ```bash
    git clone https://github.com/Hudeh/cowrywise-test.git
    cd cowrywise-test
    ```

### Running the Project

Change the env_sample file name to .env:

1. **Using docker compose**

    ```bash
    docker-compose up --build
    ```

2. **Run migrations to set up the database:**

    ```bash
    docker-compose exec frontend_api python manage.py makemigrations
    docker-compose exec frontend_api python manage.py migrate

    docker-compose exec admin_api python manage.py makemigrations
    docker-compose exec admin_api python manage.py migrate
    ```
