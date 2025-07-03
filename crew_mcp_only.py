from crewai import Agent, Task, Crew, Process
from crewai_tools import MCPServerAdapter
from mcp import StdioServerParameters
from pydantic import BaseModel, Field
import os

# MCP Server Parameters for CrewAI
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

# These will be the available tools names:
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
def create_mermaid_graph_task(agent, context=[])->Task:            
    return Task(
        description="""
        Generate a mermaid graph TBD chart config file for the following usecase: {usecase}
                        
        Add new entities and relationships to an existing graph.
        Add properties to each entity to provide more context and detail.
        Add relationships to each entity to provide more context and detail.
        All entities MUST have at least one relationship to another entity.
        """,
        expected_output="""
        A valid Mermaid Graph TB chart config file
        
        Relationships should NOT have KEYs
        Output should NOT contain any explanatory text
        Output should NOT contain backticks
        Output should NOT contain code blocks
        Output should NOT contain mermaid styling.

        Example:

            graph TD
            %% Nodes
            Patient["Patient<br/>patientId: INTEGER | KEY<br/>name: STRING<br/>birthDate: DATE"]
            Doctor["Doctor<br/>doctorId: INTEGER | KEY<br/>name: STRING<br/>specialty: STRING"]
            Appointment["Appointment<br/>appointmentId: INTEGER | KEY<br/>appointmentDate: DATETIME<br/>reason: STRING"]
            MedicalRecord["MedicalRecord<br/>recordId: INTEGER | KEY<br/>description: STRING<br/>createdAt: DATETIME<br/>notes: TEXT"]

            %% Relationships
            Patient -->|HAS_APPOINTMENT<br/>appointmentStatus: STRING| Appointment
            Patient -->|HAS_MEDICAL_RECORD<br/>recordStatus: STRING| MedicalRecord
            Doctor -->|TREATED<br/>treatmentDetails: STRING| Patient
            Appointment -->|ASSIGNED_DOCTOR<br/>appointmentReason: STRING| Doctor
            Appointment -->|CREATES_RECORD<br/>notes: TEXT| MedicalRecord
            Doctor -->|AUTHORED_RECORD<br/>signature: STRING| MedicalRecord
        """,
        agent=agent,
        context=context,
        callback=log_task_callback,  # Optional
    )

def edit_mermaid_graph_task(agent)->Task:
    return Task(
        description="""
            Modify an existing mermaid chart config file based on the given instructions. 
            
            Instructions: 
            {instructions}
            
            Existing mermaid config: 
            {mermaid_config}

            Relationships should NOT have KEYs
            Output should NOT contain any explanatory text
            Output should NOT contain backticks
            Output should NOT contain code blocks
            Output should NOT contain mermaid styling.
        """,
        expected_output="A valid Mermaid Graph TB chart config file",
        agent=agent,
        callback=log_task_callback,  # Optional
    )

def combine_mermaid_graph_task(agent)->Task:
    return Task(
        description="""
            Combine the existing mermaid chart config file with the new mermaid chart config file.
            
            Existing mermaid config: 
            {mermaid_config}
            
            New mermaid config: 
            {new_mermaid_config}

            Relationships should NOT have KEYs
            Output should NOT contain any explanatory text
            Output should NOT contain backticks
            Output should NOT contain code blocks
            Output should NOT contain mermaid styling.
        """,
        expected_output="A valid Mermaid Graph TB chart config file",
        agent=agent,
        callback=log_task_callback,  # Optional
    )

def combine_mermaid_graph_task_with_context(agent, context)->Task:
    return Task(
        description="""
            Combine the existing mermaid chart config file with the new mermaid chart config file received from context.

            Relationships should NOT have KEYs
            Output should NOT contain any explanatory text
            Output should NOT contain backticks
            Output should NOT contain code blocks
            Output should NOT contain mermaid styling.
        """,
        expected_output="A valid Mermaid Graph TB chart config file",
        agent=agent,
        context=context,
        callback=log_task_callback,  # Optional
    )

def read_data_task(agent)->Task:
    return Task(
            description="""
                Read the existing schema and data of the neo4j database.
            """,
            expected_output="The existing schema and data of the neo4j database",
            agent=agent,
            callback=log_task_callback,  # Optional
        )

# def generate_data_task_with_recommendations(agent, context)->Task:    
#     # Mermaid graph will be passed as input
#     return Task(
#         description="""
#             Construct and upload a synthetic graph dataset based on the existing schema, a mermaid chart config file, and recommended list of node details.

#             Source mermaid config: 
#             {mermaid_config}

#             Recommended node details: 
#             {recommendations}

#             Fill in property values with plausable names and sensible descriptions.
#             All nodes MUST have one relationship to at least one other node.
#         """,
#         expected_output="A string status report of the data upload process",
#         agent=agent,
#         context=context,
#         callback=log_task_callback,  # Optional
#     )

# def generate_data_task_with_context(agent, context)->Task:    
#     # Mermaid graph will be passed as input
#     return Task(
#         description="""
#             Construct and upload a synthetic graph dataset based on the existing schema, a mermaid chart config file, and recommended list of node details.

#             Fill in property values with plausable names and sensible descriptions.
#             All nodes MUST have one relationship to at least one other node.
#         """,
#         expected_output="A string status report of the data upload process",
#         agent=agent,
#         context=context,
#         callback=log_task_callback,  # Optional
#     )

def generate_data_task_with_context(agent, context)->Task: 
    # Mermaid graph and counts will be passed in from prior tasks
    return Task(
        description="""
            Add and upload a synthetic graph dataset, based on the existing schema and data of the neo4j database, a given mermaid chart config file, and recommended list of nodes.
            
            Fill in node property details with creative and interesting data, including plausable names and sensible descriptions for the usecase.
            All nodes MUST have at least one relationship to another node.
        """,
        expected_output="A string status report of the data upload process",
        agent=agent,
        context=context,
        callback=log_task_callback,  # Optional
    )

def trim_orphan_nodes_task(agent)->Task:
    return Task(
        description="""
            Delete all nodes with no relationships.
        """,
        expected_output="A string status report of the graph trimming process",
        agent=agent,
        callback=log_task_callback,  # Optional
    )

# MCP Only functions
def create_mermaid_graph(usecase: str):
    """
    Create a data model and return either a Mermaid graph
    """
    with MCPServerAdapter(server_params) as tools:

        print(f"Available tools from Stdio MCP server: {[tool.name for tool in tools]}")
                
        read_agent = mcp_agent([tools["get_neo4j_schema"], tools["read_neo4j_cypher"]])
        read_task = read_data_task(read_agent)

        # TODO
        # Create mermaid graph of existing data
        mermaid_agent = mcp_agent([tools["get_mermaid_config_str"]])
        existing_mermaid_task = create_mermaid_graph_task(mermaid_agent, [read_task])

        # TODO
        # Create mermaid graph of usecase
        usecase_mermaid_task = create_mermaid_graph_task(mermaid_agent, [read_task])

        # TODO
        # Composite mermaid graphs
        composite_mermaid_task = combine_mermaid_graph_task(mermaid_agent, [existing_mermaid_task, usecase_mermaid_task])

        # agent = mcp_agent(tools["get_mermaid_config_str"]])
        # task = create_mermaid_graph_task(agent, [composite_mermaid_task])

        crew = Crew(
            agents=[read_agent, mermaid_agent],
            tasks=[read_task, existing_mermaid_task, usecase_mermaid_task, composite_mermaid_task],
            process=Process.sequential,
            verbose=True,
        )
        inputs = {
            'usecase': usecase
        }
        result = crew.kickoff(inputs=inputs)
        return result

def edit_mermaid_graph(instructions: str, mermaid_config: str):
    """Edit a mermaid chart config file."""
    with MCPServerAdapter(server_params) as tools:
        print(f"Available tools from Stdio MCP server: {[tool.name for tool in tools]}")
        
        agent = mcp_agent([tools["validate_data_model"], tools["get_mermaid_config_str"]])

        task = edit_mermaid_graph_task(agent)

        inputs = {
            'instructions': instructions,
            'mermaid_config': mermaid_config
        }
        
        try:
            crew = Crew(
                agents=[agent],
                tasks=[task],
                process=Process.sequential,
                verbose=True,
            )
            result = crew.kickoff(inputs=inputs)
            return result
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"Error details: {error_trace}")
            raise Exception(f"An error occurred while running the crew: {str(e)}\n\nTraceback:\n{error_trace}")


def combine_mermaid_graphs(mermaid_config: str, new_mermaid_config: str):
    """Edit a mermaid chart config file."""
    with MCPServerAdapter(server_params) as tools:
        print(f"Available tools from Stdio MCP server: {[tool.name for tool in tools]}")
        
        agent = mcp_agent([tools["validate_data_model"], tools["get_mermaid_config_str"]])

        task = combine_mermaid_graph_task(agent)

        inputs = {
            'mermaid_config': mermaid_config,
            'new_mermaid_config': new_mermaid_config
        }
        
        try:
            crew = Crew(
                agents=[agent],
                tasks=[task],
                process=Process.sequential,
                verbose=True,
            )
            result = crew.kickoff(inputs=inputs)
            return result
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"Error details: {error_trace}")
            raise Exception(f"An error occurred while running the crew: {str(e)}\n\nTraceback:\n{error_trace}")

# Models for structured outputs
# class RecommendedNodeSpecs(BaseModel):
#     label: str = Field(description="Label or category of the node (ie Employee)")
#     description: str = Field(description="Description of the node (ie a person who works for a company)")
#     properties: list[str] = Field(description="List of properties for the node. Always include an 'id' and 'name'")
#     count: int = Field(description="Number of nodes to generate")

# class Recommendations(BaseModel):
#     nodes: list[RecommendedNodeSpecs]

# def recommendation_task(agent)->Task:
#     """Mermaid graph will need to be passed in as input"""
#     description = """
#         Analyze the following mermaid graph and determine the minimum number of nodes needed to create a comprehensive graph dataset.
                            
#         Mermaid graph: 
#         {mermaid_graph}

#         Return a list of data about 3x the minimum number deteremined, to create a comprehensive yet interesting graph dataset.
        
#         Example Output:

#         [
#             { label: "Employee", description: "A person who works for a company", properties: ["id", "name", "email"], count: 25 },
#             { label: "Company", description: "A business entity", properties: ["id", "name"], count: 3 }
#             { label: "Location", description: "A physical location", properties: ["id", "name", "address"], count: 1 }
#         ]
#         """
#     return Task(
#         description=description,
#         expected_output="A list of dictionaries with recommended node labels, description, properties (as a list of strings), and counts",
#         output_json=Recommendations,
#         agent=agent,
#         callback=log_task_callback,  # Optional
#     )

# def recommendation_task_with_context(agent, context)->Task:
#     # Mermaid graph will be passed from the prior task
#     description = """
#         Analyze the following mermaid graph and determine the minimum number of nodes needed to create a comprehensive graph dataset.

#         Return a list of data about 3x the minimum number deteremined, to create a comprehensive yet interesting graph dataset.
        
#         Example Output:

#         [
#             { label: "Employee", description: "A person who works for a company", properties: ["id", "name", "email"], count: 25 },
#             { label: "Company", description: "A business entity", properties: ["id", "name"], count: 3 }
#             { label: "Location", description: "A physical location", properties: ["id", "name", "address"], count: 1 }
#         ]
#     """
#     return Task(
#         description=description,
#         expected_output="A list of dictionaries with recommended node labels, description, properties (as a list of strings), and counts",
#         output_json=Recommendations,
#         agent=agent,
#         context=context,
#         callback=log_task_callback,  # Optional
#     )

# # Recommendation Agent
# def recommendation_agent()-> Agent:
#     return Agent(
#         role="Graph Data Expert",
#         goal="Recommend the lable and number of nodes needed to create a comprehensive graph dataset for the given mermaid graph.",
#         backstory="I am an expert in graph data and can recommend the number of nodes needed to create a comprehensive graph dataset.",
#         reasoning=False,  # Optional
#         verbose=False,  # Optional
#         step_callback=log_step_callback,  # Optional
#     )

# def generate_recommendations(mermaid_graph: str):
#     """Generate a recommendation for the number of nodes needed to create a comprehensive graph dataset."""
#     with MCPServerAdapter(server_params) as tools:
#         print(f"Available tools from Stdio MCP server: {[tool.name for tool in tools]}")
        
#         try:
#             agent = recommendation_agent()
#             task = recommendation_task(agent)
#             crew = Crew(
#                 agents=[agent],
#                 tasks=[task],
#                 process=Process.sequential,
#                 verbose=True,
#             )
#             inputs = {
#                 'mermaid_graph': mermaid_graph
#             }
#             result = crew.kickoff(inputs=inputs)
#             return result
#         except Exception as e:
#             import traceback
#             error_trace = traceback.format_exc()
#             print(f"Error details: {error_trace}")
#             raise Exception(f"An error occurred while running the crew: {str(e)}\n\nTraceback:\n{error_trace}")


def graph_agent()-> Agent:
    return Agent(
        role="Graph Data Expert",
        goal="Generate records from a mermaid chart config file.",
        backstory="I am an expert in graph data and can synthesize plausable mock data for graph datasets.",
        reasoning=False,  # Optional
        verbose=False,  # Optional
        step_callback=log_step_callback,  # Optional
    )

def generate_records_task(agent, context)->Task:
    """Generate records from a mermaid chart config file."""
    description = """
        Generate records from a mermaid chart config file.
        
        Mermaid graph: 
        {mermaid_graph}

        Records MUST contain an 'id' property. Values are integers starting from 1.
        Records MUST contain a 'name' property. Unique and appropriate for the node label.
        Any properties referring to another node MUST use the 'id' property of the other node.
        Output should ONLY be a list of dictionaries.
        Output should NOT contain any explanatory text.
        Output should NOT contain any backticks.
        Output should NOT contain any code blocks.

        Example output:
        [
            {
                "label":"Employee",
                "id": 1,
                "name": "Jean Luc Picard",
                "description": "Captain of the USS Enterprise",
                "email": "captain.picard@starfleet.com",
            },
            {
                "label":"Employee",
                "id": 2,
                "name": "Data",
                "description": "A humanoid android created by Dr. Noonien Soong",
                "email": "data@starfleet.com",
            }
        ]
    """
    return Task(
        description=description,
        expected_output="A list of dictionaries containing node details (label, id, name, description, and any other relevant properties)",
        agent=agent,
        context=context,
        callback=log_task_callback,  # Optional
    )

def generate_records_task_with_context(agent, context)->Task:
    """Generate records from a mermaid chart config file."""
    description = """
        Generate records from a mermaid chart config file.

        Records MUST contain an 'id' property. Values are integers starting from 1.
        Records MUST contain a 'name' property. Unique and appropriate for the node label.
        Any properties referring to another node MUST use the 'id' property of the other node.
        Output should ONLY be a list of dictionaries.
        Output should NOT contain any explanatory text.
        Output should NOT contain any backticks.
        Output should NOT contain any code blocks.

        Example output:
        [
            {
                "label":"Employee",
                "id": 1,
                "name": "Jean Luc Picard",
                "description": "Captain of the USS Enterprise",
                "email": "captain.picard@starfleet.com",
            },
            {
                "label":"Employee",
                "id": 2,
                "name": "Data",
                "description": "A humanoid android created by Dr. Noonien Soong",
                "email": "data@starfleet.com",
            }
        ]
    """
    return Task(
        description=description,
        expected_output="A list of dictionaries containing node details (label, id, name, description, and any other relevant properties)",
        agent=agent,
        context=context,
        callback=log_task_callback,  # Optional
    )

def generate_records(mermaid_graph: str):
    """Generate records from a mermaid chart config file."""
    with MCPServerAdapter(server_params) as tools:
        print(f"Available tools from Stdio MCP server: {[tool.name for tool in tools]}")
        
        try:
            read_agent = mcp_agent([tools["get_neo4j_schema"], tools["read_neo4j_cypher"]])
            read_task = read_data_task(read_agent)

            agent = graph_agent()
            task = generate_records_task(agent, [read_task])
            crew = Crew(
                agents=[agent],
                tasks=[task],
                process=Process.sequential,
                verbose=True,
            )
            inputs = {
                'mermaid_graph': mermaid_graph
            }
            result = crew.kickoff(inputs=inputs)
            return result
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"Error details: {error_trace}")
            raise Exception(f"An error occurred while running the crew: {str(e)}\n\nTraceback:\n{error_trace}")

def generate_data_task(agent, context)->Task:
    """Generate data from a mermaid chart config file."""
    description = """
        Generate data from a mermaid graph and list of records.
        
        Mermaid graph: 
        {mermaid_graph}

        Records: 
        {records}

        Create relationships between nodes based on the Mermaid graph and relevant record properties.
    """
    return Task(
        description=description,
        expected_output="A list of dictionaries containing node details (label, id, name, description, and any other relevant properties)",
        agent=agent,
        context=context,
        callback=log_task_callback,  # Optional
    )

def generate_data_task_with_context(agent, context)->Task:
    """Generate data from a mermaid chart config file."""
    description = """
        Generate data from a mermaid graph and list of records.

        Create relationships between nodes based on the Mermaid graph and relevant record properties.
    """
    return Task(
        description=description,
        expected_output="A list of dictionaries containing node details (label, id, name, description, and any other relevant properties)",
        agent=agent,
        context=context,
        callback=log_task_callback,  # Optional
    )

from neo4j import GraphDatabase

def trim_orphan_nodes() -> str:
    """Removes any nodes that are not connected to any other nodes"""
    
    neo4j_uri = os.getenv("NEO4J_URI")
    neo4j_user = os.getenv("NEO4J_USERNAME")
    neo4j_password = os.getenv("NEO4J_PASSWORD")
    
    with GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password)) as driver:
        cypher_query = "MATCH (n) WHERE NOT (n)--() DELETE n"
        result = driver.execute_query(cypher_query)
        return result

def generate_data(mermaid_graph: str, records: list[dict]):
    """Generate data from a mermaid chart config file."""

    with MCPServerAdapter(server_params) as tools:

        print(f"Available tools from Stdio MCP server: {[tool.name for tool in tools]}")
        
        try:

            # Two step process works better
            # When combined sometimes the agent/task won't do the final upload to Neo4j
            read_agent = mcp_agent([tools["get_neo4j_schema"], tools["read_neo4j_cypher"]])
            write_agent = mcp_agent([tools["write_neo4j_cypher"]])

            read_task = read_data_task(read_agent)
            write_task = generate_data_task(write_agent, [read_task])

            crew = Crew(
                    agents=[read_agent, write_agent],
                    tasks=[read_task, write_task],  # Use the instantiated task objects
                    process=Process.sequential,
                    verbose=True,
                )
            
            inputs = {
                'mermaid_graph': mermaid_graph,
                'records': records
            }

            result = crew.kickoff(inputs=inputs)

            # Optionally remove unconnected nodes here
            trim_orphan_nodes()
            
            return result
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"Error details: {error_trace}")
            raise Exception(f"An error occurred while running the crew: {str(e)}\n\nTraceback:\n{error_trace}")

def generate_data_for_usecase(usecase: str):
    with MCPServerAdapter(server_params) as tools:
        print(f"Available tools from Stdio MCP server: {[tool.name for tool in tools]}")
        
        try:

            # Read existing schema
            read_agent = mcp_agent([tools["get_neo4j_schema"], tools["read_neo4j_cypher"]])
            schema_task = read_data_task(read_agent)

            # Generate the Data Model
            data_modeling_agent = mcp_agent([tools["validate_data_model"], tools["get_mermaid_config_str"]])
            data_modeling_task = create_mermaid_graph_task(data_modeling_agent, [schema_task])
            
            # Generate recommended nodes and counts
            records_agent = graph_agent() 
            records_task = generate_records_task_with_context(records_agent, [data_modeling_task])

            # Generate the Data
            read_task = read_data_task(read_agent)
            write_agent = mcp_agent([tools["write_neo4j_cypher"]])
            write_task = generate_data_task_with_context(write_agent, [read_task, data_modeling_task, records_task])

            # Trim any orphaned nodes
            # Uncomment if wanting to use the MCP servers to do this instead
            # trim_task = trim_orphan_nodes_task(write_agent)

            # Create crew instance with configurations
            crew = Crew(
                agents=[data_modeling_agent, read_agent, write_agent],
                tasks=[schema_task, data_modeling_task, records_task, read_task, write_task],
                process=Process.sequential,
                verbose=True,
            )

            inputs = {
                'usecase': usecase
            }
            result = crew.kickoff(inputs=inputs)

            # Trim any orphaned nodes using Neo4j's bolt driver
            trim_orphan_nodes()

            return result
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"Error details: {error_trace}")
            raise Exception(f"An error occurred while running the crew: {str(e)}\n\nTraceback:\n{error_trace}")
