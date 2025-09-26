.PHONY: dev test run seed check
dev:
	pip install -r requirements.txt
test:
	pytest -q
run:
	export PYTHONPATH=. && python -c "from storefront_chatbot.app.app import build; build().launch(server_name='0.0.0.0', server_port=7860)"
seed:
	python storefront_chatbot/scripts/seed_data.py
check:
	python storefront_chatbot/scripts/check_compliance.py
