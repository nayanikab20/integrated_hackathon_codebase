import os
import json
import logging
from typing import Optional, Dict, List, Any
from pathlib import Path

from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeOutputOption, AnalyzeResult
from azure.core.credentials import AzureKeyCredential
from openai import AzureOpenAI
from dotenv import load_dotenv


class PDFAnalyzer:
    """
    End-to-end pipeline for analyzing PDF documents using Azure Document Intelligence
    and extracting metrics using Azure OpenAI.
    """
    
    def __init__(self, config_path: str = "D:/office_Work_shennanigans/hackathon/integrated_hackathon_codebase/config/config.json"):
        """
        Initialize the PDF analyzer with configuration and Azure clients.
        
        Args:
            config_path: Path to the configuration JSON file
        """
        load_dotenv("D:/office_Work_shennanigans/hackathon/integrated_hackathon_codebase/.env")
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()
        
        # Initialize Azure clients
        self.doc_intelligence_client = self._init_document_intelligence_client()
        self.openai_client = self._init_openai_client()
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from JSON file."""
        try:
            with open(config_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in configuration file: {config_path}")
    
    def _setup_logging(self) -> logging.Logger:
        """Set up logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        # Reduce Azure SDK logging verbosity
        azure_loggers = [
            'azure.core.pipeline.policies.http_logging_policy',
            'azure.ai.documentintelligence',
            'azure.core'
        ]
        
        for logger_name in azure_loggers:
            logging.getLogger(logger_name).setLevel(logging.WARNING)
            
        return logging.getLogger(__name__)
    
    def _init_document_intelligence_client(self) -> DocumentIntelligenceClient:
        """Initialize Azure Document Intelligence client."""
        endpoint = os.getenv("AZURE_DOC_INTELLIGENCE_ENDPOINT")
        key = os.getenv("AZURE_DOC_INTELLIGENCE_KEY")
        
        if not endpoint or not key:
            raise ValueError("Azure Document Intelligence credentials not found in environment variables")
        
        return DocumentIntelligenceClient(
            endpoint=endpoint,
            credential=AzureKeyCredential(key)
        )
    
    def _init_openai_client(self) -> AzureOpenAI:
        """Initialize Azure OpenAI client."""
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        key = os.getenv("AZURE_OPENAI_API_KEY")
        api_version = os.getenv("AZURE_OPENAI_API_VERSION")
        
        if not all([endpoint, key, api_version]):
            raise ValueError("Azure OpenAI credentials not found in environment variables")
        
        return AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=key,
            api_version=api_version
        )
    
    def analyze_pdf(self, 
                   pdf_path: str,
                   user_prompt_path: str,
                   system_prompt_path: str,
                   output_filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Main pipeline method to analyze PDF and extract metrics.
        
        Args:
            pdf_path: Path to the PDF file to analyze
            user_prompt_path: Path to the user prompt file
            system_prompt_path: Path to the system prompt file
            output_filename: Optional custom output filename
            
        Returns:
            Dictionary containing extracted metrics
        """
        try:
            self.logger.info(f"Starting PDF analysis for: {pdf_path}")
            
            # Load prompts
            user_prompt = self._load_prompt_file(user_prompt_path)
            system_prompt = self._load_prompt_file(system_prompt_path)
            
            # Process system prompt with quarter information
            system_prompt = self._inject_prompt_variables(system_prompt)
            
            # Extract tables from PDF
            self.logger.info("Extracting tables from PDF...")
            result = self._extract_tables_from_pdf(pdf_path)
            
            # Convert tables to markdown
            self.logger.info("Converting tables to markdown...")
            markdown_output = self._generate_markdown_from_tables(result)
            
            # Process with OpenAI
            self.logger.info("Processing with Azure OpenAI...")
            response_content = self._process_with_openai(system_prompt, user_prompt, markdown_output)
            
            # Parse and save results
            metrics_json = self._parse_response(response_content)
            output_path = self._save_results(metrics_json, output_filename or self._generate_output_filename())
            
            self.logger.info(f"Analysis completed successfully. Results saved to: {output_path}")
            return metrics_json
            
        except Exception as e:
            self.logger.error(f"Error during PDF analysis: {str(e)}")
            raise
    
    def _load_prompt_file(self, prompt_path: str) -> str:
        """Load prompt from file."""
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
    
    def _extract_tables_from_pdf(self, pdf_path: str) -> AnalyzeResult:
        """Extract tables from PDF using Azure Document Intelligence."""
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        with open(pdf_path, "rb") as f:
            poller = self.doc_intelligence_client.begin_analyze_document(
                "prebuilt-layout", body=f
            )
            result = poller.result()
        
        self.logger.info(f"Extracted {len(result.tables)} tables from PDF")
        
        # Log table information
        for table_idx, table in enumerate(result.tables):
            self.logger.debug(
                f"Table {table_idx}: {table.row_count} rows, {table.column_count} columns"
            )
        
        return result
    
    def _generate_markdown_from_tables(self, result: AnalyzeResult) -> str:
        """Convert extracted tables to markdown format."""
        markdown_tables = []

        for table_idx, table in enumerate(result.tables):
            # Initialize a 2D list to hold cell contents
            table_matrix = [["" for _ in range(table.column_count)] for _ in range(table.row_count)]

            # Fill the matrix with content
            for cell in table.cells:
                row = cell.row_index
                col = cell.column_index
                table_matrix[row][col] = cell.content.strip()

            # Convert matrix to markdown
            header = "| " + " | ".join(table_matrix[0]) + " |"
            separator = "| " + " | ".join(["---"] * table.column_count) + " |"
            rows = ["| " + " | ".join(row) + " |" for row in table_matrix[1:]]

            markdown = f"### Table {table_idx + 1}\n\n" + "\n".join([header, separator] + rows)
            markdown_tables.append(markdown)

        return "\n\n".join(markdown_tables)
    
    def _process_with_openai(self, system_prompt: str, user_prompt: str, document_text: str) -> str:
        """Process the document with Azure OpenAI."""
        deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
        if not deployment_name:
            raise ValueError("Azure OpenAI deployment name not found in environment variables")
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"{user_prompt}\n\nDocument Text:\n{document_text}"}
        ]
        
        response = self.openai_client.chat.completions.create(
            model=deployment_name,
            messages=messages,
            max_tokens=4000,
            temperature=0  # Low temperature for factual analysis
        )
        
        return response.choices[0].message.content
    
    def _parse_response(self, response_content: str) -> Dict[str, Any]:
        """Parse the OpenAI response as JSON."""
        try:
            return json.loads(response_content)
        except json.JSONDecodeError:
            self.logger.warning("Response was not valid JSON. Saving raw content.")
            return {"raw_output": response_content}
    
    def _save_results(self, metrics_json: Dict[str, Any], output_filename: str) -> str:
        """Save results to JSON file."""
        output_path = Path(output_filename)
        
        with open(output_path, "w") as f:
            json.dump(metrics_json, f, indent=2)
        
        return str(output_path)
    
    def _generate_output_filename(self) -> str:
        """Generate output filename based on configuration."""
        latest_quarter = self.config.get("latest_quarter", "unknown")
        return f"output_metrics_{latest_quarter}.json"
    
    def _inject_prompt_variables(self, base_prompt: str) -> str:
        """Inject quarter variables into the prompt."""
        latest_quarter = self.config.get("latest_quarter")
        if not latest_quarter:
            raise ValueError("latest_quarter not found in configuration")
        
        quarters = self.compute_past_5_quarters(latest_quarter)
        quarter_list = ", ".join(quarters)
        quarter_json_keys = ", ".join([f'"{q}": ""' for q in quarters])
        
        return (
            base_prompt.replace("{{quarter_list}}", quarter_list)
                      .replace("{{quarter_json_keys}}", quarter_json_keys)
        )
    
    @staticmethod
    def compute_past_5_quarters(latest_quarter: str) -> List[str]:
        """
        Compute the past 5 quarters based on the latest quarter.
        
        Args:
            latest_quarter: String in format "Q1'24"
            
        Returns:
            List of quarters in chronological order
        """
        qtr, year = latest_quarter[0:2], latest_quarter[2:]
        qtr_num = int(qtr[1])  # Extract the number from Q1, Q2, etc.
        year = int(year)

        quarters = []
        for i in range(5):
            q = qtr_num - i
            y = year
            if q <= 0:
                q += 4
                y -= 1
            quarters.append(f"Q{q}{y}")
        
        return list(reversed(quarters))  # Maintain chronological order


# Utility functions that can be used independently
def validate_file_paths(*file_paths: str) -> None:
    """Validate that all file paths exist."""
    for path in file_paths:
        if not os.path.exists(path):
            raise FileNotFoundError(f"File not found: {path}")


def create_output_directory(output_path: str) -> None:
    """Create output directory if it doesn't exist."""
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)