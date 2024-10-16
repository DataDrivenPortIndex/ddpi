
SHELL=/bin/bash

venv:  ## Set up virtual environment
	pip install -r requirements.txt

install: venv
	maturin develop -m Cargo.toml

install-release: venv
	maturin develop --release -m Cargo.toml

clean:
	-@rm -r venv
	-@cargo clean