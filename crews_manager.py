from crewai import Agent, Task, Crew, Process
from crewai_tools import MCPServerAdapter
from crews.crew_create_mermaid import CreateMermaidCrew
from crews.crew_edit_mermaid import EditMermaidCrew
from mcp import StdioServerParameters
from neo4j import GraphDatabase
import warnings
import os

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

server_params=[
    StdioServerParameters(
        command="uvx", 
        args=["mcp-neo4j-data-modeling@0.1.1", "--transport", "stdio" ],
        env=os.environ,
    ),
    StdioServerParameters(
        command="uvx",
        args=["mcp-neo4j-cypher"],
        env=os.environ,
    ),
]

# Available tools names:
# ['validate_node', 'validate_relationship', 'validate_data_model', 'load_from_arrows_json', 'export_to_arrows_json', 'get_mermaid_config_str', 'get_node_cypher_ingest_query', 'get_relationship_cypher_ingest_query', 'get_constraints_cypher_queries', 'get_neo4j_schema', 'read_neo4j_cypher', 'write_neo4j_cypher']

# Optionally logging callbacks from Agents & Tasks
def log_step_callback(output):
    print(
        f"""
        Step completed!
        details: {output.__dict__}
    """
    )

def log_task_callback(output):
    print(
        f"""
        Task completed!
        details: {output.__dict__}
    """
    )

# Agent definitions
def mcp_agent(tools):
    return Agent(
        role="MCP Tool User",
        goal="Utilize tools from MCP servers.",
        backstory="I can connect to MCP servers and use their tools.",
        tools=tools,
        reasoning=False,  # Optional
        verbose=False,  # Optional
        step_callback=log_step_callback,  # Optional
    )

# Task definitions
def read_data_task(agent)->Task:
    return Task(
            description="""
                Read the existing schema and data of the neo4j database.
            """,
            expected_output="The existing schema and data of the neo4j database",
            agent=agent,
            callback=log_task_callback,  # Optional
        )

def generate_cypher_task(agent, context)->Task:
    # Create cypher ingest queries
    return Task(
        description="""
            Create mock data as cypher queries from the context data and following mermaid graph:

            {mermaid_graph}
        """,
        expected_output="Parameterized Cypher query for bulk ingestion (using $records)",
        agent=agent,
        context=context,
        callback=log_task_callback,  # Optional
    )

def generate_cypher_task_with_context(agent, context)->Task:
    # Create cypher ingest queries
    return Task(
        description="""
            Create mock data as cypher queries from the context data
        """,
        expected_output="Parameterized Cypher query for bulk ingestion (using $records)",
        agent=agent,
        context=context,
        callback=log_task_callback,  # Optional
    )

def generate_data_task(agent, context)->Task:    
    # Mermaid graph will be passed as input
    return Task(
        description="""
            Construct and upload a synthetic graph dataset, based on context data and following mermaid graph:

            Source mermaid config: 
            {mermaid_config}

            MAKE CERTAIN to create a connected graph (where all nodes have a path to all other nodes).
            Add additional Nodes and Relationships to create a connected graph.
        """,
        expected_output="A string status report of the data upload process",
        agent=agent,
        context=context,
        callback=log_task_callback,  # Optional
    )

def generate_data_task_with_context(agent, context)->Task: 
    # Mermaid graph and counts will be passed in from prior tasks
    return Task(
        description="""
            Add and upload a synthetic graph dataset based on the context data.
            
            MAKE CERTAIN to create a connected graph (where all nodes have a path to all other nodes).
            Add additional Nodes and Relationships to create a connected graph.
        """,
        expected_output="A string status report of the data upload process",
        agent=agent,
        context=context,
        callback=log_task_callback,  # Optional
    )

def expanded_mermaid_graph_task(agent, context)->Task: 
    # Mermaid graph and counts will be passed in from prior tasks
    return Task(
        description="""
            Expand the existing graph dataset based on the context data.
            
            MAKE CERTAIN to create a connected graph (where all nodes have a path to all other nodes).
            Add additional Nodes and Relationships to create a connected graph.
        """,
        expected_output="A string status report of the data upload process",
        agent=agent,
        context=context,
        callback=log_task_callback,  # Optional
    )

# Convenience Neo4j Function
def trim_orphan_nodes() -> str:
    """Removes any nodes that are not connected to any other nodes - using the Neo4j driver"""
    
    neo4j_uri = os.getenv("NEO4J_URI")
    neo4j_user = os.getenv("NEO4J_USERNAME")
    neo4j_password = os.getenv("NEO4J_PASSWORD")
    
    with GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password)) as driver:
        cypher_query = "MATCH (n) WHERE NOT (n)--() DELETE n"
        result = driver.execute_query(cypher_query)
        return result

# MCP powered functions
def create_mermaid_graph(usecase: str, entities: list[str] = [], relationships: list[str]= []):
    """
    Create a data model and return either a Mermaid graph
    """
    with MCPServerAdapter(server_params) as tools:

        print(f"Available tools from Stdio MCP server: {[tool.name for tool in tools]}")
                
        crew = CreateMermaidCrew([tools["get_neo4j_schema"], tools["read_neo4j_cypher"],tools["validate_data_model"], tools["get_mermaid_config_str"]]).crew()

        inputs = {
            'usecase': usecase,
            'entities': entities,
            'relationships': relationships
        }
        result = crew.kickoff(inputs=inputs)
        return result

def edit_mermaid_graph(instructions: str, mermaid_config: str):
    """Edit a mermaid chart config file."""
    with MCPServerAdapter(server_params) as tools:
        print(f"Available tools from Stdio MCP server: {[tool.name for tool in tools]}")
        
        try: 
            
            crew = EditMermaidCrew([tools["validate_data_model"], tools["get_mermaid_config_str"]]).crew()
            
            inputs = {
                'instructions': instructions,
                'mermaid_config': mermaid_config
            }

            result = crew.kickoff(inputs=inputs)
            return result
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"Error details: {error_trace}")
            raise Exception(f"An error occurred while running the crew: {str(e)}\n\nTraceback:\n{error_trace}")

def generate_data(mermaid_graph: str):
    """Generate data from a mermaid chart config file."""

    with MCPServerAdapter(server_params) as tools:

        print(f"Available tools from Stdio MCP server: {[tool.name for tool in tools]}")
        
        try:

            # Two step process works better
            # When combined sometimes the agent/task won't do the final upload to Neo4j
            read_agent = mcp_agent([tools["get_neo4j_schema"], tools["read_neo4j_cypher"], tools["get_mermaid_config_str"]])
            cypher_agent = mcp_agent([tools["get_node_cypher_ingest_query"], tools["get_relationship_cypher_ingest_query"]])
            write_agent = mcp_agent([tools["write_neo4j_cypher"]])
            
            read_task = read_data_task(read_agent)
            cypher_task = generate_cypher_task(cypher_agent, [read_task])
            write_task = generate_data_task(write_agent, [cypher_task])

            crew = Crew(
                    agents=[read_agent, write_agent],
                    tasks=[read_task, write_task],  # Use the instantiated task objects
                    process=Process.sequential,
                    verbose=True,
                )
            
            inputs = {
                'mermaid_config': mermaid_graph,
            }

            result = crew.kickoff(inputs=inputs)
            return result
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"Error details: {error_trace}")
            raise Exception(f"An error occurred while running the crew: {str(e)}\n\nTraceback:\n{error_trace}")

def generate_data_for_usecase(usecase: str):
    "Creates a graph data set from a single usce case prompt"

    with MCPServerAdapter(server_params) as tools:
        print(f"Available tools from Stdio MCP server: {[tool.name for tool in tools]}")
        
        try:

            # Read existing schema
            read_agent = mcp_agent([tools["get_neo4j_schema"], tools["read_neo4j_cypher"]])
            schema_task = read_data_task(read_agent)

            # Generate the Data Model
            data_modeling_agent = mcp_agent([tools["validate_data_model"], tools["get_mermaid_config_str"]])
            data_modeling_task = create_mermaid_graph_task_context_only(data_modeling_agent, [schema_task])
            
            # Generate recommended nodes and counts
            cypher_agent = mcp_agent([tools["get_node_cypher_ingest_query"], tools["get_relationship_cypher_ingest_query"]])
            cypher_task = generate_cypher_task_with_context(cypher_agent, [data_modeling_task])

            # Generate the Data
            write_agent = mcp_agent([tools["write_neo4j_cypher"]])
            write_task = generate_data_task_with_context(write_agent, [cypher_task])

            # Trim any unconnected nodes using MCP Server
            # trim_task = trim_orphan_nodes_task(write_agent)

            # Create crew instance with configurations
            crew = Crew(
                agents=[read_agent,data_modeling_agent,cypher_agent, write_agent],
                tasks=[schema_task, data_modeling_task, cypher_task, write_task],
                process=Process.sequential,
                verbose=True,
            )

            inputs = {
                'usecase': usecase
            }

            result = crew.kickoff(inputs=inputs)

            # Trim unconnected nodes using Python driver
            trim_orphan_nodes()

            return result
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"Error details: {error_trace}")
            raise Exception(f"An error occurred while running the crew: {str(e)}\n\nTraceback:\n{error_trace}")

def expand_data_for_usecase(usecase: str):
    with MCPServerAdapter(server_params) as tools:
        print(f"Available tools from Stdio MCP server: {[tool.name for tool in tools]}")
        
        try:

            # Read existing schema
            read_agent = mcp_agent([tools["get_neo4j_schema"], tools["read_neo4j_cypher"]])
            schema_task = read_data_task(read_agent)

            # Generate the Data Model
            data_modeling_agent = mcp_agent([tools["validate_data_model"], tools["get_mermaid_config_str"]])
            data_modeling_task = expanded_mermaid_graph_task(data_modeling_agent, [schema_task])
            
            # Generate recommended nodes and counts
            cypher_agent = mcp_agent([tools["get_node_cypher_ingest_query"], tools["get_relationship_cypher_ingest_query"]])
            cypher_task = generate_cypher_task_with_context(cypher_agent, [data_modeling_task])

            # Generate the Data
            write_agent = mcp_agent([tools["write_neo4j_cypher"]])
            write_task = generate_data_task_with_context(write_agent, [cypher_task])

            # Trim any orphaned nodes
            # trim_task = trim_orphan_nodes_task(write_agent)

            # Create crew instance with configurations
            crew = Crew(
                agents=[read_agent,data_modeling_agent,cypher_agent, write_agent],
                tasks=[schema_task, data_modeling_task, cypher_task, write_task],
                process=Process.sequential,
                verbose=True,
            )

            inputs = {
                'usecase': usecase
            }
            result = crew.kickoff(inputs=inputs)

            trim_orphan_nodes()

            return result
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"Error details: {error_trace}")
            raise Exception(f"An error occurred while running the crew: {str(e)}\n\nTraceback:\n{error_trace}")