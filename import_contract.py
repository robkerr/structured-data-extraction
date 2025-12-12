import argparse
import json
import os
import sys
from datetime import datetime
from typing import List, Optional, Literal
from pathlib import Path

import isodate
import tiktoken
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

CLAUSE_TYPES = [
    "Renewal & Termination",
    "Confidentiality & Non-Disclosure",
    "Non-Compete & Exclusivity",
    "Liability & Indemnification",
    "Service-Level Agreements"
]

# Clause type definitions to help with categorization
CLAUSE_TYPE_DEFINITIONS = """
- Renewal & Termination: Covers contract duration, renewal terms, termination conditions, notice periods, auto-renewal clauses
- Confidentiality & Non-Disclosure: Covers protection of confidential information, NDAs, data privacy, information security
- Non-Compete & Exclusivity: Covers non-compete agreements, exclusivity provisions, restrictions on competing activities
- Liability & Indemnification: Covers liability limits, indemnification obligations, warranties, damages, insurance requirements, penalty clauses
- Service-Level Agreements: Covers performance metrics, service standards, quality requirements, deliverables, support obligations
"""

class Clause(BaseModel):
    """
    Represents a clause in a contract
    """

    summary: str = Field(
        ...,
        description="Concise summary of the clause content in third person, no pronouns. Focus on key obligations, rights, or restrictions."
    )
    clause_type: Literal[
        "Renewal & Termination",
        "Confidentiality & Non-Disclosure",
        "Non-Compete & Exclusivity",
        "Liability & Indemnification",
        "Service-Level Agreements"
    ] = Field(
        ...,
        description=f"The type of clause based on its primary purpose:\n{CLAUSE_TYPE_DEFINITIONS}"
    )
    
class Location(BaseModel):
    """
    Represents a physical location including address, city, state, and country.
    """

    address: Optional[str] = Field(
        None, description="The street address of the location. Use None if not provided in the contract."
    )
    city: Optional[str] = Field(
        None, description="The city of the location. Use None if not provided in the contract."
    )
    state: Optional[str] = Field(
        None, description="The state, province, or region of the location. Use None if not provided in the contract."
    )
    country: str = Field(
        ...,
        description="The country using ISO 3166-1 alpha-2 two-letter code (e.g., 'US' for United States, 'CN' for China, 'GB' for United Kingdom).",
    )


class Organization(BaseModel):
    """
    Represents an organization, including its name and location.
    """

    name: str = Field(..., description="The name of the organization.")
    location: Location = Field(
        ..., description="The primary location of the organization."
    )
    role: str = Field(
        ...,
        description="The role of the organization in the contract, such as 'provider', 'client', 'supplier', etc.",
    )


CONTRACT_TYPES = [
    "Affiliate Agreement",
    "Development",
    "Distributor",
    "Endorsement",
    "Franchise",
    "Hosting",
    "IP",
    "Joint Venture",
    "License Agreement",
    "Maintenance",
    "Manufacturing",
    "Marketing",
    "Non Compete/Solicit",
    "Outsourcing",
    "Promotion",
    "Reseller",
    "Service",
    "Sponsorship",
    "Strategic Alliance",
    "Supply",
    "Transportation",
]


class Contract(BaseModel):
    """
    Represents the key details of the contract.
    """

    summary: str = Field(
        ...,
        description=(
            "A factual, objective summary of the contract in 2-4 sentences. "
            "Include: what the agreement is about, the main obligations, and key terms. "
            "Write in third person without pronouns (they/it/this). "
            "Example: 'The agreement establishes a partnership between Company A and Company B for software development services. "
            "Company A will provide development resources while Company B provides project management. "
            "The contract runs for 2 years with a total value of $500,000.'"
        ),
    )
    contract_type: Literal[
        "Affiliate Agreement",
        "Development",
        "Distributor",
        "Endorsement",
        "Franchise",
        "Hosting",
        "IP",
        "Joint Venture",
        "License Agreement",
        "Maintenance",
        "Manufacturing",
        "Marketing",
        "Non Compete/Solicit",
        "Outsourcing",
        "Promotion",
        "Reseller",
        "Service",
        "Sponsorship",
        "Strategic Alliance",
        "Supply",
        "Transportation"
    ] = Field(..., description="The primary type of contract. Choose the single best match from the provided options.")
    parties: List[Organization] = Field(
        ...,
        description="All parties (organizations or individuals) that are signatories to the contract, with their roles clearly identified.",
    )
    effective_date: str = Field(
        ...,
        description=(
            "The date when the contract becomes effective, in YYYY-MM-DD format. "
            "Look for phrases like 'effective date', 'commencement date', 'signed on', or the signature date. "
            "If only the year is mentioned (e.g., 2015), use 2015-01-01. "
            "If only month and year (e.g., March 2015), use 2015-03-01. "
            "Extract the date from the contract text, not from external sources."
        ),
    )
    contract_scope: str = Field(
        ...,
        description="A concise description of what the contract covers: services to be provided, products delivered, rights granted, or activities permitted. Include any notable limitations or exclusions.",
    )
    duration: Optional[str] = Field(
        None,
        description=(
            "The length of the contract in ISO 8601 duration format. "
            "Examples: 'P1Y' (1 year), 'P2Y6M' (2 years 6 months), 'P18M' (18 months), 'P90D' (90 days). "
            "If the contract specifies 'until terminated' or 'perpetual', use None. "
            "Only include the initial term, not renewal periods."
        ),
    )

    end_date: Optional[str] = Field(
        None,
        description=(
            "The specific date when the contract expires or terminates, in YYYY-MM-DD format. "
            "Look for explicit end dates, expiration dates, or termination dates. "
            "If the contract specifies a duration but no end date, leave this as None (it will be calculated). "
            "If only the year is mentioned, use YYYY-01-01 format."
        ),
    )
    total_amount: Optional[float] = Field(
        None, description="The total monetary value of the contract in the contract's currency. Extract the number only, without currency symbols."
    )
    governing_law: Optional[Location] = Field(
        None, description="The jurisdiction whose laws govern the contract. Look for 'governing law', 'jurisdiction', or 'laws of [location]' clauses."
    )
    clauses: Optional[List[Clause]] = Field(
        None, description=(
            "Extract 5-10 of the most important clauses from the contract. "
            "Focus on substantive terms that affect rights, obligations, liabilities, or termination. "
            "Categorize each clause according to its primary purpose using the provided clause types."
        )
    )


def num_tokens_from_string(string: str, encoding_name: str = "cl100k_base") -> int:
    """Returns the number of tokens in a text string."""
    encoding = tiktoken.get_encoding(encoding_name)
    num_tokens = len(encoding.encode(string))
    return num_tokens

def is_valid_date(date_string):
    try:
        datetime.strptime(date_string, '%Y-%m-%d')
        return True
    except:
        return False

def add_duration_to_date(date_str, duration_str):
    """
    Add an ISO 8601 duration to a date string.
    
    Args:
        date_str (str): Date in format 'YYYY-MM-DD'
        duration_str (str): Duration in ISO 8601 format (e.g., 'P1Y2M3DT4H5M6S')
    
    Returns:
        str: Resulting date in format 'YYYY-MM-DD'
    
    Examples:
        >>> add_duration_to_date('2023-01-15', 'P1Y')
        '2024-01-15'
        >>> add_duration_to_date('2023-01-15', 'P1M')
        '2023-02-15'
        >>> add_duration_to_date('2023-01-15', 'P10D')
        '2023-01-25'
    """
    # Parse the date string
    date_obj = datetime.strptime(date_str, "%Y-%m-%d")
    
    # Parse the duration string using isodate
    duration = isodate.parse_duration(duration_str)
    
    # Add the duration to the date
    result_date = date_obj + duration
    
    # Format the result as 'YYYY-MM-DD'
    return result_date.strftime("%Y-%m-%d")

def process_contract(llm, contract_text, file_id):
    """
    Process a contract and extract structured data using LLM.

    Args:
        llm: The language model instance
        contract_text: The contract text to process
        file_id: The identifier for the file being processed

    Returns:
        dict: Structured contract data
    """
    # Create a clear instruction prompt
    extraction_prompt = f"""Extract structured information from the contract document below.

CRITICAL INSTRUCTIONS:
1. SUMMARY: Write a factual 2-4 sentence summary describing what this contract is about, who the parties are, and what the main terms are. DO NOT write meta-commentary about the task itself.
2. DATES: Look carefully for actual dates in the contract (signing dates, effective dates, commencement dates). Extract the actual date mentioned in the document.
3. DURATION: Convert duration phrases to ISO 8601 format (e.g., "one year" → "P1Y", "6 months" → "P6M", "2 years" → "P2Y", "18 months" → "P18M")
4. COUNTRY CODES: Always use 2-letter ISO codes (US, CN, GB, FR, DE, JP, etc.) never full country names
5. CLAUSE TYPES: Read each clause carefully and categorize based on what it primarily addresses:
   - "Renewal & Termination" for renewal, termination, or contract duration clauses
   - "Liability & Indemnification" for liability limits, indemnification, warranties, penalties, damages, or performance bonds
   - "Confidentiality & Non-Disclosure" for confidentiality, NDAs, or data protection
   - "Non-Compete & Exclusivity" for non-compete or exclusivity provisions
   - "Service-Level Agreements" for performance metrics, service standards, or quality requirements
6. Extract 5-10 of the most important substantive clauses

CONTRACT DOCUMENT:
{contract_text}

Now extract the contract details."""

    try:
        structured_data = llm.with_structured_output(Contract).invoke(extraction_prompt)
        structured_data = json.loads(structured_data.model_dump_json())
    except Exception as e:
        print(f"Error processing contract: {e}")
        return {"file_id": file_id, "error": str(e)}

    structured_data["file_id"] = file_id

    # Clean dates
    structured_data["effective_date"] = structured_data["effective_date"] if is_valid_date(structured_data["effective_date"]) else None
    structured_data["end_date"] = structured_data["end_date"] if is_valid_date(structured_data["end_date"]) else None

    # Infer end date
    if not structured_data["end_date"] and (structured_data["effective_date"] and structured_data["duration"]):
        try:
            structured_data["end_date"] = add_duration_to_date(structured_data["effective_date"], structured_data["duration"])
        except:
            pass

    return structured_data    


def main():
    # Load environment variables from .env file
    load_dotenv()

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description="Extract structured information from contract documents using LLM"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Path to the contract text file to process"
    )
    args = parser.parse_args()

    contract_file_path = args.input

    # Verify file exists
    if not os.path.exists(contract_file_path):
        print(f"Error: File not found: {contract_file_path}")
        sys.exit(1)

    # Get Azure OpenAI configuration from environment
    azure_endpoint = os.getenv("FOUNDRY_MODEL_ENDPOINT")
    api_key = os.getenv("OPENAI_API_KEY")
    deployment_name = os.getenv("DEPLOYMENT_NAME")

    # Print the configuration for debugging
    print(f"Azure Endpoint: {azure_endpoint}")
    print(f"Deployment Name: {deployment_name}")


    if not all([azure_endpoint, api_key, deployment_name]):
        print("Error: Missing required environment variables (FOUNDRY_MODEL_ENDPOINT, OPENAI_API_KEY, DEPLOYMENT_NAME)")
        sys.exit(1)

    llm = ChatOpenAI(
        base_url=azure_endpoint,
        api_key=api_key,
        model=deployment_name,
        temperature=0
    )

    print("Testing LLM connection with sample text...")
    try:
        test_result = llm.with_structured_output(Contract).invoke(
            "Tomaz works with Neo4j since 2017 and will make a billion dollar until 2030. The contract was signed in Las Vegas"
        )
        print("LLM connection successful!")
    except Exception as e:
        print(f"Error testing LLM connection: {e}")
        sys.exit(1)

    # Read contract text from file
    print(f"\nReading contract from: {contract_file_path}")
    with open(contract_file_path, 'r', encoding='utf-8') as f:
        contract_text = f.read()

    # Count tokens
    token_count = num_tokens_from_string(contract_text)
    print(f"Contract file: {os.path.basename(contract_file_path)}")
    print(f"Token count: {token_count}")

    # Process the contract
    print("\nProcessing contract...")
    file_id = Path(contract_file_path).stem  # Use filename without extension as ID
    structured_data = process_contract(llm, contract_text, file_id)

    # Create output directory if it doesn't exist
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)

    # Save to JSON file
    output_file = output_dir / f"{file_id}_extracted.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(structured_data, f, indent=2, ensure_ascii=False)

    print(f"\nExtraction complete!")
    print(f"Output saved to: {output_file}")



if __name__ == "__main__":
    main()

