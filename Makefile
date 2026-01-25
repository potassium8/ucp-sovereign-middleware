.PHONY: install test audit security clean

install:
	poetry install

test:
	poetry run pytest -v -s

security:
	@echo "--- 🛡️ RUNNING DEPENDENCY AUDIT (Safety Scan) ---"
	-poetry run safety scan
	@echo "--- 🛡️ RUNNING STATIC CODE ANALYSIS (Bandit) ---"
	poetry run bandit -r src -x tests

audit:
	@echo "--- STARTING SREN COMPLIANCE AUDIT (NOR:ECOI2530768A) ---"
	@echo "[INFO] Checking Cloud Provider Pricing Tables..."
	@poetry run python -c "from src.core.policy import STATUTORY_MAX_EGRESS_FEE; print(f'[LEGAL] Statutory Limit: {STATUTORY_MAX_EGRESS_FEE} EUR')"
	@make test
	@echo "--- AUDIT COMPLETE ---"

clean:
	rm -rf .pytest_cache
	rm -rf __pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
