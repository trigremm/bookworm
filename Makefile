
format:
	black .
	isort . 

f: format

http_server:
	python -m http.server 8000

.PHONY: format f http_server
