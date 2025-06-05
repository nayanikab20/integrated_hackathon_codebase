import os
import json
from typing import List, Dict
from pathlib import Path

def ensure_results_subdirs(output_path: str):
    """
    Ensure the results directory and all necessary subdirectories exist for the output path.
    """
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)


def create_batch_config_from_config(config_path: str, base_dir: str) -> List[Dict]:
    """
    Create batch config list from config.json and folder structure.
    Args:
        config_path: Path to config.json
        base_dir: Base directory of the project (e.g., 'D:/office_Work_shennanigans/hackathon/integrated_hackathon_codebase')
    Returns:
        List of config dicts for batch processing.
    """
    batch_config = []
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    banks = config.get("requested_bank_names", [])
    latest_quarter = config.get("latest_quarter")
    
    # Check if the documents directory for the latest_quarter exists for each bank
    for bank in banks:
        documents_dir = os.path.join(base_dir, "documents", latest_quarter, bank)
        if not os.path.exists(documents_dir):
            # raise FileNotFoundError(f"Data does not exist for quarter '{latest_quarter}' for bank '{bank}'. Expected directory: {documents_dir}")
            return

        # Find the PDF file that contains "supplement" in its name
        pdf_files = [f for f in os.listdir(documents_dir) if "supplement" in f.lower() and f.endswith('.pdf')]
        
        if not pdf_files:
            print(f"No PDF file found for {bank} in {documents_dir} with 'supplement' in the name. Skipping this bank.")
            continue 
        
        # Assuming we take the first matching PDF file
        pdf_path = os.path.join(documents_dir, pdf_files[0])
        
        user_prompt_path = os.path.join(base_dir, "prompts", bank, f"user_prompt.txt")
        system_prompt_path = os.path.join(base_dir, "prompts", "System_prompt", "system_prompt2.txt")
        output_path = os.path.join(base_dir, "results", latest_quarter, bank, f"{bank}.json")
        
        ensure_results_subdirs(output_path)  # Ensure the output directory exists
        
        batch_config.append({
            "pdf": pdf_path,
            "user_prompt": user_prompt_path,
            "system_prompt": system_prompt_path,
            "output": output_path,
            "bank": bank
        })
    
    return batch_config

def create_consolidated_results(batch_config: List[Dict], consolidated_output_path: str):
    """
    Aggregate individual bank results into a consolidated_results.json.
    Args:
        batch_config: List of config dicts (must include 'output' and 'bank')
        consolidated_output_path: Path to save the consolidated JSON
    """
    consolidated = {"banks": {}}
    for config in batch_config:
        bank = config["bank"]
        output_path = config["output"]
        if not os.path.exists(output_path):
            print(f"Warning: Output file not found for {bank}: {output_path}")
            continue
        with open(output_path, 'r') as f:
            bank_data = json.load(f)
        consolidated["banks"][bank] = bank_data
    with open(consolidated_output_path, 'w') as f:
        json.dump(consolidated, f, indent=2)
    print(f"Consolidated results saved to {consolidated_output_path}") 