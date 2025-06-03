from flask import Flask, request, jsonify
import os
from utils import create_batch_config_from_config, create_consolidated_results
from pdf_analyzer import PDFAnalyzer  # Assuming you have a PDFAnalyzer class for processing

app = Flask(__name__)

@app.route('/api/analyze', methods=['POST'])
def analyze():
    data = request.json
    bank_names = data.get('bank_names')  # Get the list of bank names
    config_path = data.get('config_path')
    base_dir = data.get('base_dir')

    if not bank_names or not config_path or not base_dir:
        return jsonify({"error": "Missing bank_names, config_path, or base_dir"}), 400

    # Create batch config based on the provided bank names
    batch_config = create_batch_config_from_config(config_path, base_dir)

    # Initialize the PDFAnalyzer
    analyzer = PDFAnalyzer(config_path=config_path)

    # Process each bank and trigger the analysis
    results = []
    for bank in bank_names:
        # Here you would run the analysis for each bank
        try:
            # Assuming analyze_pdf is a method that processes the PDF for the bank
            result = analyzer.analyze_pdf(
                pdf_path=batch_config[bank]['pdf'],
                user_prompt_path=batch_config[bank]['user_prompt'],
                system_prompt_path=batch_config[bank]['system_prompt'],
                output_filename=batch_config[bank]['output']
            )
            results.append(result)
        except Exception as e:
            return jsonify({"error": f"Failed to analyze {bank}: {str(e)}"}), 500

    # Create consolidated results
    latest_quarter = "Q1'2025"  # This should be dynamically fetched from your config
    consolidated_output_path = os.path.join(base_dir, "results", latest_quarter, "consolidated_results.json")
    create_consolidated_results(batch_config, consolidated_output_path)

    return jsonify({"message": "Analysis completed successfully", "output_path": consolidated_output_path}), 200

if __name__ == '__main__':
    app.run(debug=True)
