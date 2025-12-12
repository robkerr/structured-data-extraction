# Contract Data Extraction Tool

A Python command-line tool that uses LLMs to extract structured information from contract documents and outputs the data as JSON.

## Overview

This tool processes contract text files and extracts key information including:
- Contract summary and type
- Parties involved (with addresses and roles)
- Effective dates and duration
- Contract scope
- Important clauses (categorized by type)
- Governing law
- Total contract value

The extraction uses Azure AI Foundry's GPT-oss-120b model via LangChain with structured output to ensure consistent, schema-validated results.

## Features

- **Structured Extraction**: Uses Pydantic models to ensure consistent output format
- **Smart Date Parsing**: Handles various date formats and converts to ISO 8601
- **Clause Categorization**: Automatically categorizes clauses into predefined types
- **ISO Standards**: Uses ISO 3166-1 alpha-2 country codes and ISO 8601 duration format
- **Token Counting**: Reports token usage for each contract processed
- **Automatic Directory Creation**: Creates output directory if it doesn't exist

## Installation

1. Clone this repository or download the files

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up your environment variables:
   - Copy `.env.example` to `.env`
   - Fill in your Azure AI Foundry credentials

## Configuration

Create a `.env` file with the following variables:

```env
FOUNDRY_MODEL_ENDPOINT=https://your-foundry-endpoint.azure.com/openai/v1
OPENAI_API_KEY=your-api-key-here
DEPLOYMENT_NAME=gpt-oss-120b
```

See `.env.example` for a template.

## Usage

### Basic Usage

```bash
python import_contract.py --input path/to/contract.txt
```

### Example

```bash
python import_contract.py --input "contracts/my_contract.txt"
```

### Help

```bash
python import_contract.py --help
```

## Output

The tool generates JSON files in the `output/` directory with the naming pattern:
```
{filename}_extracted.json
```

### Output Schema

```json
{
  "summary": "Contract summary...",
  "contract_type": "Service",
  "parties": [
    {
      "name": "Company Name",
      "location": {
        "address": "123 Street",
        "city": "City",
        "state": "State",
        "country": "US"
      },
      "role": "Provider"
    }
  ],
  "effective_date": "2023-01-01",
  "contract_scope": "Description of what the contract covers...",
  "duration": "P1Y",
  "end_date": "2024-01-01",
  "total_amount": 100000.00,
  "governing_law": {
    "country": "US"
  },
  "clauses": [
    {
      "summary": "Clause summary...",
      "clause_type": "Renewal & Termination"
    }
  ],
  "file_id": "contract_filename"
}
```

## Clause Types

The tool categorizes clauses into the following types:

- **Renewal & Termination**: Contract duration, renewal terms, termination conditions
- **Confidentiality & Non-Disclosure**: Protection of confidential information, NDAs
- **Non-Compete & Exclusivity**: Non-compete agreements, exclusivity provisions
- **Liability & Indemnification**: Liability limits, indemnification, warranties, penalties
- **Service-Level Agreements**: Performance metrics, service standards, quality requirements

## Contract Types

Supported contract types include:
- Affiliate Agreement
- Development
- Distributor
- Endorsement
- Franchise
- Hosting
- IP
- Joint Venture
- License Agreement
- Maintenance
- Manufacturing
- Marketing
- Non Compete/Solicit
- Outsourcing
- Promotion
- Reseller
- Service
- Sponsorship
- Strategic Alliance
- Supply
- Transportation

## Requirements

- Python 3.8+
- Azure AI Foundry access with GPT-oss-120b deployment
- See `requirements.txt` for Python package dependencies

## Troubleshooting

### Authentication Errors

If you see authentication errors, verify:
1. Your `.env` file exists and contains valid credentials
2. The `FOUNDRY_MODEL_ENDPOINT` URL is correct
3. The `OPENAI_API_KEY` is valid and not expired

### File Not Found

Ensure the input file path is correct and the file exists. Use quotes around paths with spaces:
```bash
python import_contract.py --input "contracts/file with spaces.txt"
```

### Poor Extraction Quality

For better results:
- Ensure the input file is clean text (not scanned images)
- Remove excessive formatting or special characters
- Verify the contract is in English (or adjust prompts for other languages)

## License

This project is provided as-is for contract analysis purposes.

## Contributing

To improve extraction quality, you can:
1. Adjust field descriptions in the Pydantic models
2. Refine the extraction prompt in the `process_contract()` function
3. Add additional clause types or contract types to the enums

## Credit

The code in this example repo is based on an approach to processing CUAD_v1 posted by
[Tomaz Bratanic Blog Post](https://towardsdatascience.com/agentic-graphrag-for-commercial-contracts/) on his blog.