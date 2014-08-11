.PHONY: bootstrap docs load runserver shell test

bootstrap:
	mysqladmin -h localhost -u root -pmysql drop lobbying
	mysqladmin -h localhost -u root -pmysql create lobbying
	python example/manage.py syncdb
	python example/manage.py build_lobbying
	python example/manage.py collectstatic --noinput
	python example/manage.py runserver

docs:
	cd docs && make livehtml

load:
	python example/manage.py build_lobbying

runserver:
	python example/manage.py runserver

shell:
	python example/manage.py shell

test:
	pep8 lobbying
	pyflakes lobbying
	coverage run setup.py test
	coverage report -m
