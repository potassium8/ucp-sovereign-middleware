.PHONY: install test audit clean

install:
	poetry install

test:
	poetry run pytest -v -s

audit:
	@echo "--- STARTING SREN COMPLIANCE AUDIT (NOR:ECOI2530768A) ---"
	@echo "[INFO] Checking Cloud Provider Pricing Tables..."
	@poetry run python -c "from src.core.policy import STATUTORY_MAX_EGRESS_FEE; print(f'[LEGAL] Statutory Limit: {STATUTORY_MAX_EGRESS_FEE} EUR')"
	@echo "[INFO] Simulating Attack Vector..."
	@make test
	@echo "--- AUDIT COMPLETE ---"

clean:
	rm -rf .pytest_cache
	rm -rf __pycache__
