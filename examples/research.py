"""Run after local wheel installation or pip install -e ., and setup."""
from linxsci_scholar import ScholarClient

client = ScholarClient()
print(client.search('graph neural networks').json())
# Select actual IDs from your response; do not assume response field names.
print(client.paper('arxiv:2301.07041', 'toc').json())
