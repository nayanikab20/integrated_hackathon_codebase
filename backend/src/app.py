from flask import Flask, request, jsonify
import os
from utils import create_batch_config_from_config, create_consolidated_results
from pdf_analyzer import PDFAnalyzer  # Assuming you have a PDFAnalyzer class for processing
from dashboard_method_summary_analysis import create_dashboard
import json

app = Flask(__name__)

@app.route('/api/analyze', methods=['POST'])
def analyze():
    data = request.json
    bank_names = data.get('bank_names')  # Get the list of bank names
    latest_quarter = data.get('quarter')
    base_dir = "D:\office_Work_shennanigans\hackathon\integrated_hackathon_codebase"
    config_path = os.path.join(base_dir, "config", "config.json") # add a step where the data from the request populates the config

    if not bank_names or not latest_quarter:
        return jsonify({"error": "Missing bank_names or latest_quarter"}), 400

    # Add requested bank names and quarterto the configuration
    # with open(config_path, 'r') as f:
    #     config = json.load(f)
    config = {}
    config['requested_bank_names'] = bank_names
    config['latest_quarter'] = latest_quarter
    with open(config_path, 'w') as f:
        json.dump(config, f)

    # Create batch config based on the provided bank names
    batch_config = create_batch_config_from_config(config_path, base_dir)
    if not batch_config:
        return jsonify({"error": "Missing data"}), 400

    # Initialize the PDFAnalyzer
    analyzer = PDFAnalyzer(config_path=config_path)

    # Process each bank and trigger the analysis
    results = []
    for i, config in enumerate(batch_config):
        if config['bank'] in bank_names:
            # Here you would run the analysis for each bank
            try:
                # Assuming analyze_pdf is a method that processes the PDF for the bank
                result = analyzer.analyze_pdf(
                    pdf_path=config['pdf'],
                    user_prompt_path=config['user_prompt'],
                    system_prompt_path=config['system_prompt'],
                    output_filename=config['output']
                )
                results.append(result)
            except Exception as e:
                return jsonify({"error": f"Failed to analyze {config['bank']}: {str(e)}"}), 500

    # Create consolidated results
    # latest_quarter = config.get("latest_quarter")  # This should be dynamically inserted into the config
    consolidated_output_path = os.path.join(base_dir, "results", latest_quarter, "consolidated_results.json")
    create_consolidated_results(batch_config, consolidated_output_path)

    with open(consolidated_output_path, 'r') as f:
        consolidated_results = json.load(f)
    
    if consolidated_results:
        try:
            # Create dashboard with different display options
            print("🚀 Creating Banking Dashboard...")
            
            # Option 1: Save and open in browser (recommended)
            dashboard = create_dashboard(consolidated_output_path, display_mode="save_and_open")
            
            # Additional options you can use:
            print("\n🎯 Additional Display Options:")
            print("dashboard.list_components()           # List all components")
            print("dashboard.show_individual(0)         # Show first component only")
            print("dashboard.show_all_separate()        # Show all in separate tabs")
            print("dashboard.save_html('custom.html')   # Save with custom filename")

            # Read HTML file content into a string
            html_path = os.path.join(base_dir, "backend", "src", "banking_dashboard_complete.html")
            with open(html_path, "r", encoding="utf-8") as file:
                html_data = file.read()

                return jsonify({"message": "Analysis completed successfully", "output_path": consolidated_output_path, "consolidated_results": consolidated_results, "report_html": html_data}), 200
            
        except Exception as e:
            print(f"❌ An error occurred: {str(e)}")
            import traceback
            traceback.print_exc()
            return jsonify({"message": "Analysis completed successfully", "output_path": consolidated_output_path, "consolidated_results": consolidated_results}), 200
    else:
        print(f"❌ Error: File '{consolidated_output_path}' not found.") 
        return jsonify({"error": "No results found"}), 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
