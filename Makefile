run:
	python3 media_server.py

install:
	pip3 install -r requirements.txt

update:
	python3 sync_data.py

# Docker commands
restart: down build up

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

status:
	docker-compose ps