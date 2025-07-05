# CrewAI Graph Data Generator
Sample app using CrewAI + Neo4j's Data Modeling and Cypher MCP Servers to create synthetic graph datasets based on minimal user input.

## Requirements
- Python 3.12
- CrewAI
- Neo4j
- FastAPI
- uv

## Installation

```
uv sync
```

## Running
1. Start Neo4j
2. Run the app:
```
uv run fastapi run main.py --reload --port 4000 
```
or with more detailed logging:
```bash
uv run uvicorn main:app --reload --port 4000 --log-level info --use-colors
```

Interact with the API at `http://localhost:4000/docs`

## License

MIT License
See [LICENSE](LICENSE.txt) for more information.