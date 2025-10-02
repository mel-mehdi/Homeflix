run:
	python3 media_server.py

stop:
	pkill -f media_server.py

restart: stop run

install:
	pip3 install -r requirements.txt

update:
	python3 sync_data.py
