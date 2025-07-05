from fastapi import FastAPI
from crew_mcp_only import create_mermaid_graph as create_mermaid_graph_mcp_only, edit_mermaid_graph as edit_mermaid_graph_mcp_only, generate_data as generate_data_mcp_only, generate_data_for_usecase as generate_data_for_usecase_mcp_only
from fastapi.responses import Response
from fastapi import Query, HTTPException
from typing import Callable, Any, TypeVar, cast, List, Optional
from dotenv import load_dotenv
import base64
import time
import logging
import functools

# Load .env variables
load_dotenv()

# Get uvicorn logger so we can print out to the same console
uvicorn_logger = logging.getLogger("uvicorn.error")

# Type variable for generic function type
F = TypeVar('F', bound=Callable[..., Any])

def get_request_logger():
    """Get a logger that will output to Uvicorn's error stream"""
    return uvicorn_logger

# Decorator to add consistent time logging to all endpoints
def time_logging(endpoint_name: str = None):
    """
    Decorator to add consistent time logging to all endpoints.
    Automatically logs start, completion, and errors with timing information.
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Get a fresh logger for each request
            logger = get_request_logger()
            func_name = endpoint_name or func.__name__
            start_time = time.time()
            request_id = f"req_started_at_{int(start_time * 1000)}"
            
            # Log the start of the request
            logger.info(f"[{request_id}] Starting {func_name}")
            
            try:
                # Log the start of the function execution with debug info
                logger.debug(f"[{request_id}] Executing {func_name} with args: {args}")
                
                # Call the original function
                result = await func(*args, **kwargs)
                
                # Calculate and log the execution time
                total_time = time.time() - start_time
                logger.info(f"[{request_id}] {func_name} completed in {total_time:.2f}s")
                
                return result
                
            except HTTPException as e:
                # Log HTTP exceptions with timing info
                error_time = time.time() - start_time
                logger.error(
                    f"[{request_id}] HTTP error in {func_name} after {error_time:.2f}s: {str(e)}",
                    exc_info=logger.isEnabledFor(logging.DEBUG)
                )
                raise
                
            except Exception as e:
                # Log any other exceptions with full traceback if debug is enabled
                error_time = time.time() - start_time
                logger.error(
                    f"[{request_id}] Error in {func_name} after {error_time:.2f}s: {str(e)}",
                    exc_info=logger.isEnabledFor(logging.DEBUG)
                )
                raise
                
        return cast(F, wrapper)
    return decorator

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


## MCP Only Endpoints
# @app.get("/mcp_only/generate_mermaid_graph", tags=["MCP Only"])
# @time_logging("generate_mermaid_graph_mcp_only_endpoint")
# async def generate_mermaid_graph_mcp_only_endpoint(usecase: str = Query(..., 
#         description="The usecase prompt (ie healthcare, ecommerce, an employee org)", 
#         example="Employee Org"
#     )):
#     """Generate a mermaid chart config file for a given usecase using CrewAI + Neo4j MCP Servers"""

#     result = create_mermaid_graph_mcp_only(usecase)
    
#     print(f'generate_mermaid_graph_mcp_only_endpoint output: {result}')

#     # Return the raw output from CrewAI result
#     return Response(content=result.raw, media_type="text/plain")

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

    result = create_mermaid_graph_mcp_only(usecase, entities, relationships)
    
    uvicorn_logger.info(f'generate_mermaid_graph_mcp_only_endpoint output: {result}')

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

    result = edit_mermaid_graph_mcp_only(instructions, mermaid_graph)
    
    uvicorn_logger.info(f'edit_mermaid_graph_mcp_only_endpoint output: {result}')
    
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

    output = generate_data_mcp_only(mermaid_graph)
    
    return output


@app.post("/mcp_only/generate_data_for_usecase", tags=["MCP Only"])
@time_logging("generate_data_for_usecase_endpoint_mcp_only_endpoint")
async def generate_data_mcp_only_endpoint(usecase: str = Query(..., 
    description="The usecase prompt (ie healthcare, ecommerce, an employee org chart)",
    example="Sales pipeline"
)):
    """
    Generate and upload a synthetic graph dataset to Neo4j from a usecase prompt.
    This endpoint uses:
        - Neo4j's Data Modeling MCP server for creating a data model
        - Neo4j's Cypher MCP server for uploading the data.
        - CrewAI for orchestrating the process.
    """    
    output = generate_data_for_usecase_mcp_only(usecase)
    
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
    output = generate_data_for_usecase_mcp_only(usecase)
    
    return output