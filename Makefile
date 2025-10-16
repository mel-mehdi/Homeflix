# run:
# 	python3 media_server.py

# install:
# 	pip3 install -r requirements.txt

# update:
# 	python3 sync_data.py

build:
	docker-compose build

sync-now:
	docker-compose exec sync-scheduler python sync_data.py

sync-logs:
	docker-compose logs -f sync-scheduler

# Docker commands
re: build up

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

status:
	docker-compose ps