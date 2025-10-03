run:
	python3 media_server.py

stop:
	pkill -f media_server.py

restart: stop run

install:
	pip3 install -r requirements.txt

update:
	python3 sync_data.py

# Docker commands
docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-restart:
	docker-compose restart

docker-logs:
	docker-compose logs -f

docker-status:
	docker-compose ps

docker-stop:
	docker-compose stop

docker-start:
	docker-compose start

# Complete Docker setup (build and run)
docker-setup: docker-build docker-up
	@echo "Homeflix is now running in Docker!"
	@echo "Access at: http://localhost:5000"

ip:
	@echo "Your server IP address:"
	@hostname -I | awk '{print $$1}' || ip addr show | grep "inet " | grep -v 127.0.0.1 | head -1
	@echo ""
	@echo "Access Homeflix at: http://$$(hostname -I | awk '{print $$1}'):5000"
