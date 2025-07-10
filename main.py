from fastapi import FastAPI
from crews_manager import create_mermaid_graph, edit_mermaid_graph, generate_data, generate_data_for_usecase, expand_data_for_usecase
from fastapi.responses import Response
from fastapi import Query
from typing import List, Optional
from dotenv import load_dotenv
from logging_util import time_logging, get_request_logger
import base64

load_dotenv()

logger = get_request_logger()

tags_metadata = [
    {
        "name": "MCP Only",
        "description": "Generating a graph dataset using only CrewAI + Neo4j MCP Servers.",
    },
]

app = FastAPI(openapi_tags=tags_metadata)

# Root endpoint for server status
@app.get("/")
async def root():
    """Status endpoint"""
    return {"message": "CrewAI+BAML+Neo4j Synthetic Data Generator Server running"}


@app.get("/mcp_only/generate_mermaid_graph", tags=["MCP Only"])
@time_logging("generate_mermaid_graph_mcp_only_endpoint")
async def generate_mermaid_graph_mcp_only_endpoint(
    usecase: str = Query(..., 
        description="The usecase prompt (ie healthcare, ecommerce, an employee org)", 
        example="Employee Org"
    ),
    entities: Optional[List[str]] = Query(None,
        description="Optional List of Nodes to include",
        example=["Employee", "Company"]),
    relationships: Optional[list[str]] = Query(None,
        description="Optional List of Relationship types to include",
        example=["SUPERVISES", "EMPLOYED_AT"])
    ):
    """Generate a mermaid chart config file for a given usecase using CrewAI + Neo4j MCP Servers"""

    result = create_mermaid_graph(usecase, entities, relationships)
    
    logger.info(f'generate_mermaid_graph_mcp_only_endpoint output: {result}')

    # Return the raw output from CrewAI result
    return Response(content=result.raw, media_type="text/plain")

@app.patch("/mcp_only/edit_mermaid_graph", tags=["MCP Only"])
@time_logging("edit_mermaid_graph_mcp_only_endpoint")
async def edit_mermaid_graph_mcp_only_endpoint(
        instructions: str = Query(..., description="The instructions for editing the mermaid graph configuration", example="Add an 'Address' node and any appropriate relationships for it"), 
        mermaid_graph_base64: str = Query(..., description="""
        Base64 encoded string of the mermaid graph configuration.
        
        Encoded example:

        graph TD
        %% Nodes
        Company["Company<br/>Id: INTEGER | KEY<br/>Name: STRING<br/>Industry: STRING"] 
        Department["Department<br/>Id: INTEGER | KEY<br/>Name: STRING<br/>Description: STRING"] 
        Manager["Manager<br/>Id: INTEGER | KEY<br/>Name: STRING"]
        Employee["Employee<br/>Id: INTEGER | KEY<br/>Name: STRING<br/>Experience: STRING<br/>ContactInfo: TEXT"] 

        %% Relationships
        Company -->|HAS_DEPARTMENT - departmentDetails STRING| Department
        Employee -->|WORKS_IN - jobTitle STRING| Department
        Manager -->|LEADS - teamGoal STRING| Department
        Employee -->|EMPLOYED_BY - companyIndustry STRING| Company
        Employee -->|MANAGED_BY - managerName STRING| Manager
        
        """, 
        example="Z3JhcGggVEQKICAgICUlIE5vZGVzCiAgICBDb21wYW55WyJDb21wYW55PGJyLz5JZDogSU5URUdFUiB8IEtFWTxici8+TmFtZTogU1RSSU5HPGJyLz5JbmR1c3RyeTogU1RSSU5HIl0gCiAgICBEZXBhcnRtZW50WyJEZXBhcnRtZW50PGJyLz5JZDogSU5URUdFUiB8IEtFWTxici8+TmFtZTogU1RSSU5HPGJyLz5EZXNjcmlwdGlvbjogU1RSSU5HIl0gCiAgICBNYW5hZ2VyWyJNYW5hZ2VyPGJyLz5JZDogSU5URUdFUiB8IEtFWTxici8+TmFtZTogU1RSSU5HIl0KICAgIEVtcGxveWVlWyJFbXBsb3llZTxici8+SWQ6IElOVEVHRVIgfCBLRVk8YnIvPk5hbWU6IFNUUklORzxici8+RXhwZXJpZW5jZTogU1RSSU5HPGJyLz5Db250YWN0SW5mbzogVEVYVCJdIAoKICAgICUlIFJlbGF0aW9uc2hpcHMKICAgIENvbXBhbnkgLS0+fEhBU19ERVBBUlRNRU5UIC0gZGVwYXJ0bWVudERldGFpbHMgU1RSSU5HfCBEZXBhcnRtZW50CiAgICBFbXBsb3llZSAtLT58V09SS1NfSU4gLSBqb2JUaXRsZSBTVFJJTkd8IERlcGFydG1lbnQKICAgIE1hbmFnZXIgLS0+fExFQURTIC0gdGVhbUdvYWwgU1RSSU5HfCBEZXBhcnRtZW50CiAgICBFbXBsb3llZSAtLT58RU1QTE9ZRURfQlkgLSBjb21wYW55SW5kdXN0cnkgU1RSSU5HfCBDb21wYW55CiAgICBFbXBsb3llZSAtLT58TUFOQUdFRF9CWSAtIG1hbmFnZXJOYW1lIFNUUklOR3wgTWFuYWdlcg==")
    ):
    """Edit a mermaid chart config file using CrewAI +Neo4j MCP Servers"""

    mermaid_graph = base64.b64decode(mermaid_graph_base64.encode()).decode('utf-8')

    result = edit_mermaid_graph(instructions, mermaid_graph)
    
    logger.info(f'edit_mermaid_graph_mcp_only_endpoint output: {result}')
    
    return Response(content=result.raw, media_type="text/plain")

@app.post("/mcp_only/generate_data", tags=["MCP Only"])
@time_logging("generate_data_endpoint_mcp_only_endpoint")
async def generate_data_endpoint_mcp_only_endpoint(
    mermaid_graph_base64: str = Query(..., 
    description="""
    Base64 encoded string of the mermaid graph configuration

    Encoded Example:

    graph TD
    %% Nodes
    Company["Company<br/>Id: INTEGER | KEY<br/>Name: STRING<br/>Industry: STRING"] 
    Department["Department<br/>Id: INTEGER | KEY<br/>Name: STRING<br/>Description: STRING"] 
    Manager["Manager<br/>Id: INTEGER | KEY<br/>Name: STRING"]
    Employee["Employee<br/>Id: INTEGER | KEY<br/>Name: STRING<br/>Experience: STRING<br/>ContactInfo: TEXT"] 

    %% Relationships
    Company -->|HAS_DEPARTMENT - departmentDetails STRING| Department
    Employee -->|WORKS_IN - jobTitle STRING| Department
    Manager -->|LEADS - teamGoal STRING| Department
    Employee -->|EMPLOYED_BY - companyIndustry STRING| Company
    Employee -->|MANAGED_BY - managerName STRING| Manager
    """,
    example="Z3JhcGggVEQKICAgICUlIE5vZGVzCiAgICBDb21wYW55WyJDb21wYW55PGJyLz5JZDogSU5URUdFUiB8IEtFWTxici8+TmFtZTogU1RSSU5HPGJyLz5JbmR1c3RyeTogU1RSSU5HIl0gCiAgICBEZXBhcnRtZW50WyJEZXBhcnRtZW50PGJyLz5JZDogSU5URUdFUiB8IEtFWTxici8+TmFtZTogU1RSSU5HPGJyLz5EZXNjcmlwdGlvbjogU1RSSU5HIl0gCiAgICBNYW5hZ2VyWyJNYW5hZ2VyPGJyLz5JZDogSU5URUdFUiB8IEtFWTxici8+TmFtZTogU1RSSU5HIl0KICAgIEVtcGxveWVlWyJFbXBsb3llZTxici8+SWQ6IElOVEVHRVIgfCBLRVk8YnIvPk5hbWU6IFNUUklORzxici8+RXhwZXJpZW5jZTogU1RSSU5HPGJyLz5Db250YWN0SW5mbzogVEVYVCJdIAoKICAgICUlIFJlbGF0aW9uc2hpcHMKICAgIENvbXBhbnkgLS0+fEhBU19ERVBBUlRNRU5UIC0gZGVwYXJ0bWVudERldGFpbHMgU1RSSU5HfCBEZXBhcnRtZW50CiAgICBFbXBsb3llZSAtLT58V09SS1NfSU4gLSBqb2JUaXRsZSBTVFJJTkd8IERlcGFydG1lbnQKICAgIE1hbmFnZXIgLS0+fExFQURTIC0gdGVhbUdvYWwgU1RSSU5HfCBEZXBhcnRtZW50CiAgICBFbXBsb3llZSAtLT58RU1QTE9ZRURfQlkgLSBjb21wYW55SW5kdXN0cnkgU1RSSU5HfCBDb21wYW55CiAgICBFbXBsb3llZSAtLT58TUFOQUdFRF9CWSAtIG1hbmFnZXJOYW1lIFNUUklOR3wgTWFuYWdlcg=="),
):
    """
    Generate and upload synthetic graph dataset to Neo4j from a Mermaid Graph TB configuration.
    
    This endpoint takes a base64 encoded mermaid graph configuration to generate data.
    """

    mermaid_graph = base64.b64decode(mermaid_graph_base64.encode()).decode('utf-8')

    output = generate_data(mermaid_graph)
    
    return output

@app.post("/mcp_only/generate_data_for_usecase", tags=["MCP Only"])
@time_logging("generate_data_for_usecase_endpoint_mcp_only_endpoint")
async def generate_data_mcp_only_endpoint(usecase: str = Query(..., 
    description="The usecase prompt (ie healthcare, ecommerce, an employee org chart)",
    example="Employee Org"
)):
    """
    Generate and upload a synthetic graph dataset to Neo4j from a usecase prompt.
    This endpoint uses:
        - Neo4j's Data Modeling MCP server for creating a data model
        - Neo4j's Cypher MCP server for uploading the data.
        - CrewAI for orchestrating the process.
    """    
    output = generate_data_for_usecase(usecase)
    
    return output

@app.post("/mcp_only/expand_data_for_usecase", tags=["MCP Only"])
@time_logging("expand_data_for_usecase_endpoint_mcp_only_endpoint")
async def expand_data_mcp_only_endpoint(usecase: str = Query(..., 
    description="The usecase prompt (ie healthcare, ecommerce, an employee org chart)",
    example="Customer Support"
)):
    """
    Generate and upload additioanl synthetic graph dataset to Neo4j from a usecase prompt.
    This endpoint uses:
        - Neo4j's Data Modeling MCP server for creating a data model
        - Neo4j's Cypher MCP server for uploading the data.
        - CrewAI for orchestrating the process.
    """    
    output = expand_data_for_usecase(usecase)
    
    return output