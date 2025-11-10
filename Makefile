# Makefile for prizepicks-correlation-ml project

.PHONY: help install test backtest-tiny backtest-nfl clean

PYTHON := python
START_DATE := 2024-09-01
END_DATE := 2024-12-31

help:
	@echo "Available commands:"
	@echo "  make install        Install Python dependencies"
	@echo "  make test          Run all tests"
	@echo "  make backtest-tiny Run small backtest for testing"
	@echo "  make backtest-nfl  Run full NFL backtest"
	@echo "  make clean         Remove cache and temp files"

install:
	pip install -r requirements.txt

test:
	pytest tests/ -v

backtest-tiny:
	$(PYTHON) -m scripts.backtest_nfl --tiny --start $(START_DATE) --end $(END_DATE)

backtest-nfl:
	$(PYTHON) -m scripts.backtest_nfl --start $(START_DATE) --end $(END_DATE)

clean:
	rm -rf data/cache/backtests/*
	rm -rf **/__pycache__
	rm -rf .pytest_cache