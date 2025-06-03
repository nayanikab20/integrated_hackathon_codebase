#!/usr/bin/env python3
"""
Main execution script for PDF analysis pipeline.
This script demonstrates how to use the PDFAnalyzer class.
"""

import sys
import argparse
from pathlib import Path
from pdf_analyzer import PDFAnalyzer, validate_file_paths, create_output_directory
import os
import json
from utils import create_batch_config_from_config, create_consolidated_results


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="Analyze PDF documents and extract financial metrics")
    parser.add_argument("--pdf", required=True, help="Path to PDF file to analyze")
    parser.add_argument("--user-prompt", required=True, help="Path to user prompt file")
    parser.add_argument("--system-prompt", required=True, help="Path to system prompt file")
    parser.add_argument("--config", default="config.json", help="Path to configuration file")
    parser.add_argument("--output", help="Custom output filename")
    parser.add_argument("--output-dir", default="./output", help="Output directory")
    
    args = parser.parse_args()
    
    try:
        # Validate input files exist
        validate_file_paths(args.pdf, args.user_prompt, args.system_prompt, args.config)
        
        # Create output directory
        create_output_directory(args.output_dir)
        
        # Initialize analyzer
        print("Initializing PDF Analyzer...")
        analyzer = PDFAnalyzer(config_path=args.config)
        
        # Generate output filename if not provided
        output_filename = args.output
        if not output_filename:
            config_name = Path(args.config).stem
            pdf_name = Path(args.pdf).stem
            output_filename = f"{args.output_dir}/metrics_{pdf_name}_{config_name}.json"
        
        # Run analysis
        print("Starting PDF analysis...")
        results = analyzer.analyze_pdf(
            pdf_path=args.pdf,
            user_prompt_path=args.user_prompt,
            system_prompt_path=args.system_prompt,
            output_filename=output_filename
        )
        
        print(f"✅ Analysis completed successfully!")
        print(f"📊 Results saved to: {output_filename}")
        
        # Display summary
        if isinstance(results, dict) and "raw_output" not in results:
            print(f"📈 Extracted {len(results)} metric categories")
        
    except FileNotFoundError as e:
        print(f"❌ File not found: {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        sys.exit(1)


def run_example():
    """
    Example function showing how to use the PDFAnalyzer programmatically.
    Uncomment and modify the file paths to match your setup.
    """
    try:
        # Example configuration
        pdf_path = "fourth-quarter-2024-earnings-supplement-wells-fargo.pdf"
        user_prompt_path = "user_prompt_wells_fargo.txt"
        system_prompt_path = "system_prompt2.txt"
        config_path = "config.json"
        
        # Validate files exist (uncomment to use)
        # validate_file_paths(pdf_path, user_prompt_path, system_prompt_path, config_path)
        
        # Initialize analyzer
        analyzer = PDFAnalyzer(config_path=config_path)
        
        # Run analysis
        results = analyzer.analyze_pdf(
            pdf_path=pdf_path,
            user_prompt_path=user_prompt_path,
            system_prompt_path=system_prompt_path,
            output_filename="example_output.json"
        )
        
        print("Example analysis completed!")
        return results
        
    except Exception as e:
        print(f"Example failed: {e}")
        return None


def batch_analyze():
    """
    Batch processing for multiple PDFs using config and utility functions.
    """
    base_dir = "D:\office_Work_shennanigans\hackathon\integrated_hackathon_codebase"
    config_path = os.path.join(base_dir, "config", "config.json")
    batch_config = create_batch_config_from_config(config_path, base_dir)
    print(batch_config)
    analyzer = PDFAnalyzer()
    results = []

    for i, config in enumerate(batch_config):
        try:
            print(f"Processing document {i+1}/{len(batch_config)}: {config['pdf']}")
            result = analyzer.analyze_pdf(
                pdf_path=config["pdf"],
                user_prompt_path=config["user_prompt"],
                system_prompt_path=config["system_prompt"],
                output_filename=config["output"]
            )
            results.append({"config": config, "result": result, "status": "success"})
            print(f"✅ Document {i+1} completed")
        except Exception as e:
            print(f"❌ Document {i+1} failed: {e}")
            results.append({"config": config, "error": str(e), "status": "failed"})

    # Summary
    successful = sum(1 for r in results if r["status"] == "success")
    failed = len(results) - successful
    print(f"\n📊 Batch processing completed: {successful} successful, {failed} failed")

    # Consolidate results
    # Load the configuration to get the latest quarter
    with open(config_path, 'r') as f:
        config = json.load(f)
    latest_quarter = config.get("latest_quarter")
    consolidated_output_path = os.path.join(base_dir, "results", latest_quarter, "consolidated_results.json")
    create_consolidated_results(batch_config, consolidated_output_path)

    return results


if __name__ == "__main__":
    # Run the main CLI interface
    # main()
    # Alternatively, uncomment one of these to run examples:
    # run_example()
    batch_analyze()