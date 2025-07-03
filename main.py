from fastapi import FastAPI, Body
from crew_mcp_only import create_mermaid_graph, edit_mermaid_graph, combine_mermaid_graphs, generate_records, generate_data, generate_data_for_usecase
from fastapi.responses import Response
from fastapi import Query, HTTPException
from typing import Callable, Any, TypeVar, cast
from dotenv import load_dotenv
from datetime import datetime
import time
import base64
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
            # Format the start time in ISO 8601 format
            iso_time = datetime.fromtimestamp(start_time).isoformat()
            request_id = f"req_started_at_{iso_time}"
            
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
@app.get("/mcp_only/generate_mermaid_graph", tags=["MCP Only"])
@time_logging("generate_mermaid_graph_mcp_only_endpoint")
async def generate_mermaid_graph_mcp_only_endpoint(usecase: str = Query(..., 
        description="The usecase prompt (ie healthcare, ecommerce, an employee org)", 
        example="Employee Org"
    )):
    """Generate a mermaid chart config file for a given usecase using CrewAI + Neo4j MCP Servers"""

    result = create_mermaid_graph(usecase)
    
    print(f'generate_mermaid_graph_mcp_only_endpoint output: {result}')

    # Return the raw output from CrewAI result
    return Response(content=result.raw, media_type="text/plain")

@app.patch("/mcp_only/edit_mermaid_graph", tags=["MCP Only"])
@time_logging("edit_mermaid_graph_mcp_only_endpoint")
async def edit_mermaid_graph_mcp_only_endpoint(
        instructions: str = Query(..., description="The instructions for editing the mermaid graph configuration", example="Add an 'Address' node and any appropriate relationships for it"), 
        mermaid_graph_base64: str = Query(..., description="Base64 encoded string of the mermaid graph configuration", 
        example="Z3JhcGggVEQKICAgICUlIE5vZGVzCiAgICBDb21wYW55WyJDb21wYW55PGJyLz5JZDogSU5URUdFUiB8IEtFWTxici8+TmFtZTogU1RSSU5HPGJyLz5JbmR1c3RyeTogU1RSSU5HIl0gCiAgICBEZXBhcnRtZW50WyJEZXBhcnRtZW50PGJyLz5JZDogSU5URUdFUiB8IEtFWTxici8+TmFtZTogU1RSSU5HPGJyLz5EZXNjcmlwdGlvbjogU1RSSU5HIl0gCiAgICBNYW5hZ2VyWyJNYW5hZ2VyPGJyLz5JZDogSU5URUdFUiB8IEtFWTxici8+TmFtZTogU1RSSU5HIl0KICAgIEVtcGxveWVlWyJFbXBsb3llZTxici8+SWQ6IElOVEVHRVIgfCBLRVk8YnIvPk5hbWU6IFNUUklORzxici8+RXhwZXJpZW5jZTogU1RSSU5HPGJyLz5Db250YWN0SW5mbzogVEVYVCJdIAoKICAgICUlIFJlbGF0aW9uc2hpcHMKICAgIENvbXBhbnkgLS0+fEhBU19ERVBBUlRNRU5UIC0gZGVwYXJ0bWVudERldGFpbHMgU1RSSU5HfCBEZXBhcnRtZW50CiAgICBFbXBsb3llZSAtLT58V09SS1NfSU4gLSBqb2JUaXRsZSBTVFJJTkd8IERlcGFydG1lbnQKICAgIE1hbmFnZXIgLS0+fExFQURTIC0gdGVhbUdvYWwgU1RSSU5HfCBEZXBhcnRtZW50CiAgICBFbXBsb3llZSAtLT58RU1QTE9ZRURfQlkgLSBjb21wYW55SW5kdXN0cnkgU1RSSU5HfCBDb21wYW55CiAgICBFbXBsb3llZSAtLT58TUFOQUdFRF9CWSAtIG1hbmFnZXJOYW1lIFNUUklOR3wgTWFuYWdlcg==")
    ):
    """Edit a mermaid chart config file using CrewAI +Neo4j MCP Servers"""

    # Example Mermaid Graph (unencoded):
    # graph TD
    #     %% Nodes
    #     Company["Company<br/>Id: INTEGER | KEY<br/>Name: STRING<br/>Industry: STRING"] 
    #     Department["Department<br/>Id: INTEGER | KEY<br/>Name: STRING<br/>Description: STRING"] 
    #     Manager["Manager<br/>Id: INTEGER | KEY<br/>Name: STRING"]
    #     Employee["Employee<br/>Id: INTEGER | KEY<br/>Name: STRING<br/>Experience: STRING<br/>ContactInfo: TEXT"] 

    #     %% Relationships
    #     Company -->|HAS_DEPARTMENT - departmentDetails STRING| Department
    #     Employee -->|WORKS_IN - jobTitle STRING| Department
    #     Manager -->|LEADS - teamGoal STRING| Department
    #     Employee -->|EMPLOYED_BY - companyIndustry STRING| Company
    #     Employee -->|MANAGED_BY - managerName STRING| Manager

    mermaid_graph = base64.b64decode(mermaid_graph_base64.encode()).decode('utf-8')

    result = edit_mermaid_graph(instructions, mermaid_graph)
        
    return Response(content=result.raw, media_type="text/plain")

@app.post("/mcp_only/combine_mermaid_graphs", tags=["MCP Only"])
@time_logging("combine_mermaid_graphs_mcp_only_endpoint")
async def combine_mermaid_graphs_mcp_only_endpoint(
    mermaid_graph_base64: str = Query(..., 
    description="Base64 encoded string of the mermaid graph configuration",
    example="Z3JhcGggVEQKICAgICUlIE5vZGVzCiAgICBDb21wYW55WyJDb21wYW55PGJyLz5JZDogSU5URUdFUiB8IEtFWTxici8+TmFtZTogU1RSSU5HPGJyLz5JbmR1c3RyeTogU1RSSU5HIl0gCiAgICBEZXBhcnRtZW50WyJEZXBhcnRtZW50PGJyLz5JZDogSU5URUdFUiB8IEtFWTxici8+TmFtZTogU1RSSU5HPGJyLz5EZXNjcmlwdGlvbjogU1RSSU5HIl0gCiAgICBNYW5hZ2VyWyJNYW5hZ2VyPGJyLz5JZDogSU5URUdFUiB8IEtFWTxici8+TmFtZTogU1RSSU5HIl0KICAgIEVtcGxveWVlWyJFbXBsb3llZTxici8+SWQ6IElOVEVHRVIgfCBLRVk8YnIvPk5hbWU6IFNUUklORzxici8+RXhwZXJpZW5jZTogU1RSSU5HPGJyLz5Db250YWN0SW5mbzogVEVYVCJdIAoKICAgICUlIFJlbGF0aW9uc2hpcHMKICAgIENvbXBhbnkgLS0+fEhBU19ERVBBUlRNRU5UIC0gZGVwYXJ0bWVudERldGFpbHMgU1RSSU5HfCBEZXBhcnRtZW50CiAgICBFbXBsb3llZSAtLT58V09SS1NfSU4gLSBqb2JUaXRsZSBTVFJJTkd8IERlcGFydG1lbnQKICAgIE1hbmFnZXIgLS0+fExFQURTIC0gdGVhbUdvYWwgU1RSSU5HfCBEZXBhcnRtZW50CiAgICBFbXBsb3llZSAtLT58RU1QTE9ZRURfQlkgLSBjb21wYW55SW5kdXN0cnkgU1RSSU5HfCBDb21wYW55CiAgICBFbXBsb3llZSAtLT58TUFOQUdFRF9CWSAtIG1hbmFnZXJOYW1lIFNUUklOR3wgTWFuYWdlcg=="),
    new_mermaid_graph_base64: str = Query(..., 
    description="Base64 encoded string of the new mermaid graph configuration",
    example="Z3JhcGggVEQKJSUgTm9kZXMKQ3VzdG9tZXJbIkN1c3RvbWVyPGJyLz5jdXN0b21lcklkOiBJTlRFR0VSIHwgS0VZPGJyLz5uYW1lOiBTVFJJTkc8YnIvPmVtYWlsOiBTVFJJTkc8YnIvPnJlZ2lzdHJhdGlvbkRhdGU6IERBVEUiXQpQcm9kdWN0WyJQcm9kdWN0PGJyLz5wcm9kdWN0SWQ6IElOVEVHRVIgfCBLRVk8YnIvPnByb2R1Y3ROYW1lOiBTVFJJTkc8YnIvPnByaWNlOiBGTE9BVDxici8+Y2F0ZWdvcnk6IFNUUklORyJdCk9yZGVyWyJPcmRlcjxici8+b3JkZXJJZDogSU5URUdFUiB8IEtFWTxici8+b3JkZXJEYXRlOiBEQVRFVElNRTxici8+dG90YWxBbW91bnQ6IEZMT0FUIl0KUGF5bWVudFsiUGF5bWVudDxici8+cGF5bWVudElkOiBJTlRFR0VSIHwgS0VZPGJyLz5wYXltZW50RGF0ZTogREFURVRJTUU8YnIvPmFtb3VudDogRkxPQVQ8YnIvPnBheW1lbnRNZXRob2Q6IFNUUklORyJdCkRlbGl2ZXJ5WyJEZWxpdmVyeTxici8+ZGVsaXZlcnlJZDogSU5URUdFUiB8IEtFWTxici8+ZGVsaXZlcnlEYXRlOiBEQVRFVElNRTxici8+c3RhdHVzOiBTVFJJTkciXQpTaGlwcGluZ1siU2hpcHBpbmc8YnIvPnNoaXBwaW5nSWQ6IElOVEVHRVIgfCBLRVk8YnIvPnNoaXBwaW5nRGF0ZTogREFURVRJTUU8YnIvPnRyYWNraW5nTnVtYmVyOiBTVFJJTkciXQoKJSUgUmVsYXRpb25zaGlwcwpDdXN0b21lciAtLT58UExBQ0VEfCBPcmRlcgpPcmRlciAtLT58Q09OVEFJTlN8IFByb2R1Y3QKQ3VzdG9tZXIgLS0+fE1BREV8IFBheW1lbnQKT3JkZXIgLS0+fEFTU09DSUFURVN8IFBheW1lbnQKT3JkZXIgLS0+fERFTElWRVJFRHwgRGVsaXZlcnkKRGVsaXZlcnkgLS0+fFNISVBQRUR8IFNoaXBwaW5n")
):
    """
    Combine two mermaid graph configurations using CrewAI + Neo4j MCP Servers
    """
    
    # Example of new Mermaid Graph (unencoded):
    # graph TD
        # %% Nodes
        # Customer["Customer<br/>customerId: INTEGER | KEY<br/>name: STRING<br/>email: STRING<br/>registrationDate: DATE"]
        # Product["Product<br/>productId: INTEGER | KEY<br/>productName: STRING<br/>price: FLOAT<br/>category: STRING"]
        # Order["Order<br/>orderId: INTEGER | KEY<br/>orderDate: DATETIME<br/>totalAmount: FLOAT"]
        # Payment["Payment<br/>paymentId: INTEGER | KEY<br/>paymentDate: DATETIME<br/>amount: FLOAT<br/>paymentMethod: STRING"]
        # Delivery["Delivery<br/>deliveryId: INTEGER | KEY<br/>deliveryDate: DATETIME<br/>status: STRING"]
        # Shipping["Shipping<br/>shippingId: INTEGER | KEY<br/>shippingDate: DATETIME<br/>trackingNumber: STRING"]

        # %% Relationships
        # Customer -->|PLACED| Order
        # Order -->|CONTAINS| Product
        # Customer -->|MADE| Payment
        # Order -->|ASSOCIATES| Payment
        # Order -->|DELIVERED| Delivery
        # Delivery -->|SHIPPED| Shipping

    mermaid_graph = base64.b64decode(mermaid_graph_base64.encode()).decode('utf-8')
    new_mermaid_graph = base64.b64decode(new_mermaid_graph_base64.encode()).decode('utf-8')

    result = combine_mermaid_graphs(mermaid_graph, new_mermaid_graph)
    
    return Response(content=result.raw, media_type="text/plain")
    

@app.post("/mcp_only/generate_records", tags=["MCP Only"])
@time_logging("generate_records_mcp_only_endpoint")
async def generate_records_mcp_only_endpoint(
    mermaid_graph_base64: str = Query(..., 
    description="Base64 encoded string of the mermaid graph configuration",
    example="Z3JhcGggVEQKICAgICUlIE5vZGVzCiAgICBDb21wYW55WyJDb21wYW55PGJyLz5JZDogSU5URUdFUiB8IEtFWTxici8+TmFtZTogU1RSSU5HPGJyLz5JbmR1c3RyeTogU1RSSU5HIl0gCiAgICBEZXBhcnRtZW50WyJEZXBhcnRtZW50PGJyLz5JZDogSU5URUdFUiB8IEtFWTxici8+TmFtZTogU1RSSU5HPGJyLz5EZXNjcmlwdGlvbjogU1RSSU5HIl0gCiAgICBNYW5hZ2VyWyJNYW5hZ2VyPGJyLz5JZDogSU5URUdFUiB8IEtFWTxici8+TmFtZTogU1RSSU5HIl0KICAgIEVtcGxveWVlWyJFbXBsb3llZTxici8+SWQ6IElOVEVHRVIgfCBLRVk8YnIvPk5hbWU6IFNUUklORzxici8+RXhwZXJpZW5jZTogU1RSSU5HPGJyLz5Db250YWN0SW5mbzogVEVYVCJdIAoKICAgICUlIFJlbGF0aW9uc2hpcHMKICAgIENvbXBhbnkgLS0+fEhBU19ERVBBUlRNRU5UIC0gZGVwYXJ0bWVudERldGFpbHMgU1RSSU5HfCBEZXBhcnRtZW50CiAgICBFbXBsb3llZSAtLT58V09SS1NfSU4gLSBqb2JUaXRsZSBTVFJJTkd8IERlcGFydG1lbnQKICAgIE1hbmFnZXIgLS0+fExFQURTIC0gdGVhbUdvYWwgU1RSSU5HfCBEZXBhcnRtZW50CiAgICBFbXBsb3llZSAtLT58RU1QTE9ZRURfQlkgLSBjb21wYW55SW5kdXN0cnkgU1RSSU5HfCBDb21wYW55CiAgICBFbXBsb3llZSAtLT58TUFOQUdFRF9CWSAtIG1hbmFnZXJOYW1lIFNUUklOR3wgTWFuYWdlcg==")

):
    """
    Generate records for a given mermaid graph configuration using CrewAI + Neo4j MCP Servers
    """
    
    # Example Mermaid Graph (unencoded):
    # graph TD
    #     %% Nodes
    #     Company["Company<br/>Id: INTEGER | KEY<br/>Name: STRING<br/>Industry: STRING"] 
    #     Department["Department<br/>Id: INTEGER | KEY<br/>Name: STRING<br/>Description: STRING"] 
    #     Manager["Manager<br/>Id: INTEGER | KEY<br/>Name: STRING"]
    #     Employee["Employee<br/>Id: INTEGER | KEY<br/>Name: STRING<br/>Experience: STRING<br/>ContactInfo: TEXT"] 

    #     %% Relationships
    #     Company -->|HAS_DEPARTMENT - departmentDetails STRING| Department
    #     Employee -->|WORKS_IN - jobTitle STRING| Department
    #     Manager -->|LEADS - teamGoal STRING| Department
    #     Employee -->|EMPLOYED_BY - companyIndustry STRING| Company
    #     Employee -->|MANAGED_BY - managerName STRING| Manager

    mermaid_graph = base64.b64decode(mermaid_graph_base64.encode()).decode('utf-8')

    result = generate_records(mermaid_graph)
        
    return Response(content=result.raw, media_type="text/plain")

# @app.post("/mcp_only/generate_recommendations", tags=["MCP Only"])
# @time_logging("generate_recommendations_mcp_only_endpoint")
# async def generate_recommendations_mcp_only_endpoint(
#     mermaid_graph_base64: str = Query(..., 
#     description="Base64 encoded string of the mermaid graph configuration",
#     example="Z3JhcGggVEQKICAgICUlIE5vZGVzCiAgICBDb21wYW55WyJDb21wYW55PGJyLz5JZDogSU5URUdFUiB8IEtFWTxici8+TmFtZTogU1RSSU5HPGJyLz5JbmR1c3RyeTogU1RSSU5HIl0gCiAgICBEZXBhcnRtZW50WyJEZXBhcnRtZW50PGJyLz5JZDogSU5URUdFUiB8IEtFWTxici8+TmFtZTogU1RSSU5HPGJyLz5EZXNjcmlwdGlvbjogU1RSSU5HIl0gCiAgICBNYW5hZ2VyWyJNYW5hZ2VyPGJyLz5JZDogSU5URUdFUiB8IEtFWTxici8+TmFtZTogU1RSSU5HIl0KICAgIEVtcGxveWVlWyJFbXBsb3llZTxici8+SWQ6IElOVEVHRVIgfCBLRVk8YnIvPk5hbWU6IFNUUklORzxici8+RXhwZXJpZW5jZTogU1RSSU5HPGJyLz5Db250YWN0SW5mbzogVEVYVCJdIAoKICAgICUlIFJlbGF0aW9uc2hpcHMKICAgIENvbXBhbnkgLS0+fEhBU19ERVBBUlRNRU5UIC0gZGVwYXJ0bWVudERldGFpbHMgU1RSSU5HfCBEZXBhcnRtZW50CiAgICBFbXBsb3llZSAtLT58V09SS1NfSU4gLSBqb2JUaXRsZSBTVFJJTkd8IERlcGFydG1lbnQKICAgIE1hbmFnZXIgLS0+fExFQURTIC0gdGVhbUdvYWwgU1RSSU5HfCBEZXBhcnRtZW50CiAgICBFbXBsb3llZSAtLT58RU1QTE9ZRURfQlkgLSBjb21wYW55SW5kdXN0cnkgU1RSSU5HfCBDb21wYW55CiAgICBFbXBsb3llZSAtLT58TUFOQUdFRF9CWSAtIG1hbmFnZXJOYW1lIFNUUklOR3wgTWFuYWdlcg==")
# ):
#     """
#     Generate recommendations for a given mermaid graph configuration using CrewAI + Neo4j MCP Servers
#     """
    
#     mermaid_graph = base64.b64decode(mermaid_graph_base64.encode()).decode('utf-8')

#     result = generate_recommendations_mcp_only(mermaid_graph)
        
#     return Response(content=result.raw, media_type="text/plain")

@app.post("/mcp_only/generate_data", tags=["MCP Only"])
@time_logging("generate_data_endpoint_mcp_only_endpoint")
async def generate_data_endpoint_mcp_only_endpoint(
    mermaid_graph_base64: str = Query(..., 
        description="Base64 encoded string of the mermaid graph configuration",
        example="Z3JhcGggVEQKICAgICUlIE5vZGVzCiAgICBDb21wYW55WyJDb21wYW55PGJyLz5JZDogSU5URUdFUiB8IEtFWTxici8+TmFtZTogU1RSSU5HPGJyLz5JbmR1c3RyeTogU1RSSU5HIl0gCiAgICBEZXBhcnRtZW50WyJEZXBhcnRtZW50PGJyLz5JZDogSU5URUdFUiB8IEtFWTxici8+TmFtZTogU1RSSU5HPGJyLz5EZXNjcmlwdGlvbjogU1RSSU5HIl0gCiAgICBNYW5hZ2VyWyJNYW5hZ2VyPGJyLz5JZDogSU5URUdFUiB8IEtFWTxici8+TmFtZTogU1RSSU5HIl0KICAgIEVtcGxveWVlWyJFbXBsb3llZTxici8+SWQ6IElOVEVHRVIgfCBLRVk8YnIvPk5hbWU6IFNUUklORzxici8+RXhwZXJpZW5jZTogU1RSSU5HPGJyLz5Db250YWN0SW5mbzogVEVYVCJdIAoKICAgICUlIFJlbGF0aW9uc2hpcHMKICAgIENvbXBhbnkgLS0+fEhBU19ERVBBUlRNRU5UIC0gZGVwYXJ0bWVudERldGFpbHMgU1RSSU5HfCBEZXBhcnRtZW50CiAgICBFbXBsb3llZSAtLT58V09SS1NfSU4gLSBqb2JUaXRsZSBTVFJJTkd8IERlcGFydG1lbnQKICAgIE1hbmFnZXIgLS0+fExFQURTIC0gdGVhbUdvYWwgU1RSSU5HfCBEZXBhcnRtZW50CiAgICBFbXBsb3llZSAtLT58RU1QTE9ZRURfQlkgLSBjb21wYW55SW5kdXN0cnkgU1RSSU5HfCBDb21wYW55CiAgICBFbXBsb3llZSAtLT58TUFOQUdFRF9CWSAtIG1hbmFnZXJOYW1lIFNUUklOR3wgTWFuYWdlcg=="),
    records: list[dict] = Body(..., 
        description="List of node records",
        example="""
[
    {
        "label": "Company",
        "id": 1,
        "name": "Tech Innovations Inc.",
        "industry": "Technology"
    },
    {
        "label": "Company",
        "id": 2,
        "name": "Health Solutions Ltd.",
        "industry": "Healthcare"
    },
    {
        "label": "Department",
        "id": 1,
        "name": "Research and Development",
        "description": "Focuses on innovation and product development."
    },
    {
        "label": "Department",
        "id": 2,
        "name": "Sales and Marketing",
        "description": "Responsible for promoting and selling products."
    },
    {
        "label": "Department",
        "id": 3,
        "name": "Human Resources",
        "description": "Manages employee relations and recruitment."
    },
    {
        "label": "Manager",
        "id": 1,
        "name": "Alice Johnson"
    },
    {
        "label": "Manager",
        "id": 2,
        "name": "Bob Smith"
    },
    {
        "label": "Employee",
        "id": 1,
        "name": "John Doe",
        "experience": "5 years",
        "contactInfo": "john.doe@email.com"
    },
    {
        "label": "Employee",
        "id": 2,
        "name": "Jane Smith",
        "experience": "3 years",
        "contactInfo": "jane.smith@email.com"
    },
    {
        "label": "Employee",
        "id": 3,
        "name": "Emily Davis",
        "experience": "2 years",
        "contactInfo": "emily.davis@email.com"
    }
]
        """
    )
):
    """
    Generate and upload synthetic graph dataset to Neo4j from a Mermaid Graph TB configuration.
    
    This endpoint takes a base64 encoded mermaid graph configuration to generate data.
    """

    # Example Mermaid Graph (unencoded):
    # graph TD
    #     %% Nodes
    #     Company["Company<br/>Id: INTEGER | KEY<br/>Name: STRING<br/>Industry: STRING"] 
    #     Department["Department<br/>Id: INTEGER | KEY<br/>Name: STRING<br/>Description: STRING"] 
    #     Manager["Manager<br/>Id: INTEGER | KEY<br/>Name: STRING"]
    #     Employee["Employee<br/>Id: INTEGER | KEY<br/>Name: STRING<br/>Experience: STRING<br/>ContactInfo: TEXT"] 

    #     %% Relationships
    #     Company -->|HAS_DEPARTMENT - departmentDetails STRING| Department
    #     Employee -->|WORKS_IN - jobTitle STRING| Department
    #     Manager -->|LEADS - teamGoal STRING| Department
    #     Employee -->|EMPLOYED_BY - companyIndustry STRING| Company
    #     Employee -->|MANAGED_BY - managerName STRING| Manager

    mermaid_graph = base64.b64decode(mermaid_graph_base64.encode()).decode('utf-8')
    
    output = generate_data(mermaid_graph, records)
    
    return output


@app.post("/mcp_only/generate_data_for_usecase", tags=["MCP Only"])
@time_logging("generate_data_for_usecase_endpoint_mcp_only_endpoint")
async def generate_data_mcp_only_endpoint(usecase: str = Query(..., 
    description="The usecase prompt (ie healthcare, ecommerce, an employee org chart)",
    example="Customer Support"
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
