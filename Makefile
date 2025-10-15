# run:
# 	python3 media_server.py

# install:
# 	pip3 install -r requirements.txt

# update:
# 	python3 sync_data.py

sync-now:
	docker-compose exec sync-scheduler python sync_data.py

sync-logs:
	docker-compose logs -f sync-scheduler

# Docker commands
re: down build up

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