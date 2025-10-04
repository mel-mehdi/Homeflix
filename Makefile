run:
	python3 media_server.py


install:
	pip3 install -r requirements.txt

update:
	python3 sync_data.py

# Docker commands
restart: stop start

build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

restart:
	docker-compose restart

logs:
	docker-compose logs -f

status:
	docker-compose ps

stop:
	docker-compose stop

start:
	docker-compose start

