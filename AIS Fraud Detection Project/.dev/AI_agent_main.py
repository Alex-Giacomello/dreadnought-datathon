"""
Shipping Fraud Detection AI Agent

[VERSION]
Event = Datathon 2025
Team = Dreadnaught
Author = Chris Matherne
version = 1.0 Beta
"""

import os
import sys
import logging
import importlib
import subprocess
# Will import serpapi after dependency check

# Function to check and install required packages
def check_and_install_dependencies():
    # Dictionary of required packages and their import names (if different)
    required_packages = {
        'python-dotenv': 'dotenv',
        'langchain-anthropic': 'langchain_anthropic',
        'langchain': 'langchain',  # Main package
        'langchain_community': 'langchain_community',  # Community integrations
        'langchain_classic': 'langchain_classic',  # Classic functionality
        'langchain_core': 'langchain_core',  # Core abstractions
        'langchain-text-splitters': 'langchain_text_splitters',  # Text processing
        'pandas': 'pandas',
        'matplotlib': 'matplotlib',
        'seaborn': 'seaborn',
        'requests': 'requests',
        'duckduckgo-search': 'duckduckgo_search',
        'folium': 'folium',
        'pydantic>=2.0.0': 'pydantic',  # Explicitly require Pydantic v2
        'packaging': 'packaging',  # For version checking
        'anthropic': 'anthropic',  # Required by langchain-anthropic
        'google-search-results': 'serpapi',  # SerpAPI package
    }
    
    missing_packages = []
    
    # Check each package
    for package, import_name in required_packages.items():
        try:
            importlib.import_module(import_name)
            print(f"[OK] {package} is installed")
        except ImportError:
            print(f"[ERROR] {package} is not installed")
            missing_packages.append(package)
    
    # Install missing packages
    if missing_packages:
        print("\nInstalling missing packages...")
        for package in missing_packages:
            print(f"Installing {package}...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"[OK] {package} installed successfully")
            except subprocess.CalledProcessError as e:
                print(f"[ERROR] Failed to install {package}: {e}")
                return False
    
    return True

# Print diagnostic information
print(f"Python version: {sys.version}")
print(f"Python executable: {sys.executable}")

# Check dependencies before importing other modules
if not check_and_install_dependencies():
    print("Error: Failed to install required dependencies. Please install them manually.")
    sys.exit(1)
    
# Print version information for key packages
try:
    import langchain
    print(f"LangChain version: {langchain.__version__}")
except (ImportError, AttributeError):
    print("LangChain not found or version info not available")
    
try:
    import langchain_core
    print(f"LangChain Core version: {langchain_core.__version__}")
except (ImportError, AttributeError):
    print("LangChain Core not found or version info not available")
    
try:
    import anthropic
    print(f"Anthropic version: {anthropic.__version__}")
except (ImportError, AttributeError):
    print("Anthropic not found or version info not available")
    
# Import SerpAPI after dependency check
from serpapi import GoogleSearch

# Verify that Pydantic v2 is installed
try:
    import pydantic
    from packaging import version
    if version.parse(pydantic.__version__) < version.parse("2.0.0"):
        print(f"[WARNING] Pydantic version {pydantic.__version__} detected. This script requires Pydantic v2.0.0 or higher.")
        print("Attempting to upgrade Pydantic...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pydantic>=2.0.0"])
        print("Please restart the script to use the upgraded Pydantic version.")
        sys.exit(1)
    else:
        print(f"[OK] Using Pydantic version {pydantic.__version__}")
except (ImportError, AttributeError):
    print("[ERROR] Could not verify Pydantic version. Please ensure Pydantic v2.0.0 or higher is installed.")
    sys.exit(1)

# Now import the required modules
from dotenv import load_dotenv

# LLM imports
from langchain_anthropic import ChatAnthropic

# LangChain imports - using latest structure
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
try:
    # Try the current recommended import path
    from langchain.agents import initialize_agent, AgentType
    print("Successfully imported from langchain.agents")
except ImportError:
    try:
        # Fall back to classic if main import fails
        from langchain_classic.agents import initialize_agent
        from langchain_classic.agents.agent_types import AgentType
        print("Successfully imported from langchain_classic.agents")
    except ImportError:
        try:
            # Try community as last resort
            from langchain_community.agents import initialize_agent
            from langchain_community.agents.agent_types import AgentType
            print("Successfully imported from langchain_community.agents")
        except ImportError:
            print("ERROR: Failed to import initialize_agent and AgentType from any LangChain package")
            sys.exit(1)

# Verify that AgentType has the expected value
try:
    if not hasattr(AgentType, "CHAT_CONVERSATIONAL_REACT_DESCRIPTION"):
        print("Warning: The AgentType class is missing CHAT_CONVERSATIONAL_REACT_DESCRIPTION.")
        print("Available AgentType values:", dir(AgentType))
        print("Will attempt to use an alternative approach.")
except Exception as e:
    print(f"Error checking AgentType: {e}")
    print("Will attempt to continue with a different initialization method.")

# Memory imports
try:
    from langchain.memory import ConversationBufferWindowMemory
except ImportError:
    try:
        from langchain_classic.memory import ConversationBufferWindowMemory
    except ImportError:
        from langchain_community.memory import ConversationBufferWindowMemory

# Import our custom tools
from tools import (
    RunSFDTool, 
    QuerySFDDataTool, 
    VesselLookupTool, 
    GenerateChartTool
)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
env_file = "AI_agent_Env.env"
print(f"Looking for environment file at: {os.path.abspath(env_file)}")
if not os.path.exists(env_file):
    print(f"Warning: Environment file {env_file} not found.")

load_dotenv(env_file)
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")

if not CLAUDE_API_KEY:
    print("Warning: CLAUDE_API_KEY not found in environment file. API calls will fail.")
else:
    # Mask the key for security
    masked_key = CLAUDE_API_KEY[:4] + "..." + CLAUDE_API_KEY[-4:] if len(CLAUDE_API_KEY) > 8 else "***"  
    print(f"API Key found with value starting with {masked_key}")


# Initialize the Claude model
if not CLAUDE_API_KEY:
    print("Error: CLAUDE_API_KEY not found or empty. Cannot initialize the model.")
    print("Please add your API key to the AI_agent_Env.env file with format: CLAUDE_API_KEY=your_key_here")
    sys.exit(1)

try:
    model = ChatAnthropic(
        model="claude-3-5-sonnet-20241022",
        anthropic_api_key=CLAUDE_API_KEY,
        temperature=0.1,
        max_tokens=4000
    )
    print("Claude model initialized successfully")
except Exception as e:
    print(f"Error initializing Claude model: {e}")
    sys.exit(1)

# Define the agent prompt
system_prompt = """
You are a research assistant that helps law enforcement to detect potential fraudulent shipping to enable focused tracking. You use historical data to identify potential fraud trends and provide results.

You have access to the following tools:
1. run_sfd - Run the SFD.py script with specified parameters
2. query_sfd_data - Query data from SFD.py output files
3. vessel_lookup - Look up vessel information online based on MMSI number
4. generate_chart - Create charts and visualizations from SFD.py data

Your primary goal is to help users analyze shipping data for potential fraud. When providing information about vessels, include links to external sources when available.

Always provide clear explanations of your findings and insights that would be useful for law enforcement purposes.
"""

# Create agent memory
memory = ConversationBufferWindowMemory(memory_key="chat_history", k=5, return_messages=True)

# Initialize the tools
tools = [
    RunSFDTool(), 
    QuerySFDDataTool(), 
    VesselLookupTool(), 
    GenerateChartTool()
]

# Create the agent with parameters compatible with classic LangChain
print("Initializing AI agent...")

# Function to handle agent initialization with different approaches
def create_agent():
    # Try different agent types that work better with structured tools
    try:
        print("Attempting agent initialization with STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION...")
        agent = initialize_agent(
            tools=tools,
            llm=model,
            agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5,
        )
        print("Successfully created agent with STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION")
        return agent
    except (ImportError, AttributeError, TypeError, ValueError) as e:
        print(f"Method 1 failed: {str(e)}")
    
    # Method 2: Try a simple zero-shot agent
    try:
        print("Attempting agent initialization with ZERO_SHOT_REACT_DESCRIPTION...")
        agent = initialize_agent(
            tools=tools,
            llm=model,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
        )
        print("Successfully created agent with ZERO_SHOT_REACT_DESCRIPTION")
        return agent
    except (ImportError, AttributeError, TypeError, ValueError) as e:
        print(f"Method 2 failed: {str(e)}")
    
    # Method 3: Try the conversational agent with modified tool format
    try:
        print("Attempting basic conversational agent initialization...")
        from langchain_classic.agents import ConversationalChatAgent, AgentExecutor
        from langchain_classic.schema import StrOutputParser
        
        # Create a simpler agent that works with the provided tools
        agent = ConversationalChatAgent.from_llm_and_tools(
            llm=model,
            tools=tools,
        )
        agent_executor = AgentExecutor.from_agent_and_tools(
            agent=agent,
            tools=tools,
            memory=memory,
            verbose=True,
            max_iterations=5,
        )
        print("Successfully created ConversationalChatAgent with AgentExecutor")
        return agent_executor
    except (ImportError, AttributeError, TypeError, ValueError) as e:
        print(f"Method 3 failed: {str(e)}")
    
    # Last resort: Try to create a simplified agent
    try:
        print("Attempting simplified agent creation...")
        # Create a basic agent chain manually
        from langchain_classic.chains import LLMChain
        from langchain_classic.prompts import PromptTemplate
        
        prompt = PromptTemplate.from_template(
            "You are an assistant that helps analyze shipping data.\n"
            "User: {input}\n"
            "Assistant: "
        )
        chain = LLMChain(llm=model, prompt=prompt)
        print("Created a simple LLMChain as fallback")
        return chain
    except Exception as e:
        print(f"All methods failed: {e}")
        raise Exception("Could not create any type of agent")

# Try to create the agent
try:
    agent = create_agent()
except Exception as e:
    print(f"ERROR: Failed to initialize agent: {e}")
    print("Unable to continue without a working agent. Please check LangChain versions and compatibility.")
    sys.exit(1)

def main():
    print("Welcome to the AIS Fraud Detection Assistant")
    print("Type 'exit' to quit")
    
    # Check if running in an interactive terminal
    import sys
    if not sys.stdin.isatty():
        print("\nNot running in an interactive terminal. Using a test query instead.")
        user_input = "What can you help me with?"
        process_input(user_input)
        return
    
    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() in ["exit", "quit"]:
                break
            process_input(user_input)
        except EOFError:
            print("\nEOF detected. Exiting.")
            break
        except KeyboardInterrupt:
            print("\nKeyboard interrupt. Exiting.")
            break

def perform_search(query):
    """Perform a web search using SerpAPI and return formatted results"""
    try:
        print("Performing web search for additional information...")
        params = {
            "engine": "google_ai_mode",
            "q": query,
            "api_key": "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"
        }

        search = GoogleSearch(params)
        results = search.get_dict()
        text_blocks = results.get("text_blocks", [])
        
        # Format the search results as a string
        if not text_blocks:
            return "No relevant search results found."
            
        # Format the first few text blocks (limit to avoid overwhelming the agent)
        formatted_results = "\n\nSearch Results:\n" + "\n\n".join(
            [block.get("snippet", "") for block in text_blocks[:5] if "snippet" in block]
        )
        
        print(f"Found {len(text_blocks)} search results")
        return formatted_results
    except Exception as e:
        print(f"Error during search: {e}")
        return "Error retrieving search results."

def process_input(user_input):
    print("\nProcessing your request...")
    try:
        # First perform a web search to augment the agent's knowledge
        search_results = perform_search(user_input)
        
        # Combine the user input with search results
        enhanced_input = f"{user_input}\n\nHere is some additional information that might help:{search_results}"
        
        # Approach 1: If agent has an invoke method (modern LangChain)
        if hasattr(agent, 'invoke'):
            print("Using invoke() method")
            try:
                response = agent.invoke({"input": enhanced_input})
                # Handle different response formats
                if isinstance(response, dict) and "output" in response:
                    print(f"Assistant: {response['output']}")
                elif isinstance(response, str):
                    print(f"Assistant: {response}")
                else:
                    print(f"Assistant: {str(response)}")
                return  # Skip the remaining approaches
            except Exception as e:
                print(f"Error with invoke() method: {e}")
                # Continue to next approach
        
        # Approach 2: If agent has a run method (older agents)
        if hasattr(agent, 'run'):
            print("Using run() method")
            try:
                response = agent.run(enhanced_input)
                print(f"Assistant: {response}")
                return  # Skip the remaining approaches
            except Exception as e:
                print(f"Error with run() method: {e}")
                # Continue to next approach
        
        # Approach 3: If agent is an LLMChain (fallback approach)
        if hasattr(agent, '__call__'):
            print("Using chain __call__")
            try:
                response = agent({"input": enhanced_input})
                if isinstance(response, dict) and "text" in response:
                    print(f"Assistant: {response['text']}")
                else:
                    print(f"Assistant: {str(response)}")
                return  # Skip the remaining approaches
            except Exception as e:
                print(f"Error with chain __call__: {e}")
                # Fall through to the error message
        
        # If we reach here, none of the approaches worked
        print("Assistant: I'm having trouble processing your request through the available mechanisms.")
        print("Please try a simpler query or contact support.")
        
    except Exception as e:
        logger.error(f"Unhandled error: {e}")
        print("Assistant: I encountered an error processing your request.")
        print(f"Error details: {str(e)}")
        print("Please try again with a different query or restart the application if the issue persists.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


# Search functionality has been integrated into the perform_search function above