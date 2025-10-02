run:
	python3 media_server.py

stop:
	pkill -f media_server.py

restart: stop run

install:
	pip3 install -r requirements.txt

update:
	python3 sync_data.py

ip:
	@echo "Your server IP address:"
	@hostname -I | awk '{print $$1}' || ip addr show | grep "inet " | grep -v 127.0.0.1 | head -1
	@echo ""
	@echo "Access Homeflix at: http://$$(hostname -I | awk '{print $$1}'):5000"
