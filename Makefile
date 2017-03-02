help:
	@echo 'Command:'
	@echo 'install    install the package.'
	@echo 'pack       pack the package only in local.'
	@echo 'upload     upload package to official pypi site.'
	@echo 'clean      clean package files.'

install:
	python setup.py install

pack:
	python setup.py sdist

upload:
	python setup.py sdist register upload
	rm -rf dist gotyou.egg-info

clean:
	rm -rf dist gotyou.egg-info
