import json
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
import os
import webbrowser
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Enhanced Bank color mapping with distinct colors for each bank
BANK_COLORS = {
    'BARCLAYS': '#00BFFF',      # Cyan/Light Blue
    'Wells Fargo': '#FF6B35',   # Orange/Red
    'JP Morgan': '#8B4513',     # Brown
    'JPMorgan Chase & Co.': '#8B4513',  # Brown (alternative name)
    'Bank of America': '#DC143C',  # Red
    'Citi': '#4169E1',          # Blue
    'Synchrony': '#FFD700',     # Gold
    'Capital One': '#228B22',   # Green
    'CHASE': '#8B4513',         # Brown
    'Citi Branded': '#4169E1',  # Blue
    'Citi Retail': '#1E90FF',   # Light Blue
    'WellsFargo': '#FF4500',    # Orange Red (alternative)
    'JPMorgan': '#A0522D',      # Sienna Brown
}

# Plotly color sequence for fallback
PLOTLY_COLORS = px.colors.qualitative.Set1 + px.colors.qualitative.Set2

def load_and_process_data(json_file_path):
    """Load JSON data and convert to structured format"""
    with open(json_file_path, 'r') as file:
        data = json.load(file)
    return data['banks']

def clean_numeric_value(value):
    """Clean and convert string values to numeric"""
    if value is None or value == "Null" or value == "" or pd.isna(value):
        return np.nan
    
    if isinstance(value, str):
        cleaned = value.replace('$', '').replace(',', '').replace('%', '').strip()
        try:
            return float(cleaned)
        except ValueError:
            return np.nan
    return float(value)

def get_quarters_from_data(banks_data):
    """Extract quarters in the order they appear in the JSON data"""
    # Get the first bank's first metric to determine the order
    for bank_name, bank_data in banks_data.items():
        for metric_category in ['metrics', 'computed_metrics']:
            if metric_category in bank_data:
                for metric_name, metric_data in bank_data[metric_category].items():
                    if isinstance(metric_data, dict) and metric_data:
                        # Return quarters in the order they appear in the JSON
                        return list(metric_data.keys())
    return []

def create_coverage_table_data(banks_data, quarters):
    """Create coverage rates table data"""
    table_data = []
    
    for bank_name, bank_data in banks_data.items():
        if 'computed_metrics' in bank_data and 'Coverage Ratio (%)' in bank_data['computed_metrics']:
            row_data = {'Bank': bank_name}
            
            # Add quarterly data
            for quarter in quarters[-6:]:  # Last 6 quarters
                value = bank_data['computed_metrics']['Coverage Ratio (%)'].get(quarter)
                row_data[quarter] = clean_numeric_value(value)
            
            # Calculate basis points change (latest vs previous) - add at the end
            if len(quarters) >= 2:
                latest_val = row_data.get(quarters[-1], np.nan)
                prev_val = row_data.get(quarters[-2], np.nan)
                if not pd.isna(latest_val) and not pd.isna(prev_val):
                    row_data['Δ Qtr (bps)'] = int((latest_val - prev_val) * 100)
                else:
                    row_data['Δ Qtr (bps)'] = np.nan
            
            table_data.append(row_data)
    
    return pd.DataFrame(table_data)

def create_ncl_coverage_table_data(banks_data, quarters):
    """Create NCL Coverage table data"""
    table_data = []
    
    for bank_name, bank_data in banks_data.items():
        if 'computed_metrics' in bank_data and 'Net Credit Loss Coverage' in bank_data['computed_metrics']:
            row_data = {'Bank': bank_name}
            
            # Add quarterly data
            for quarter in quarters[-6:]:  # Last 6 quarters
                value = bank_data['computed_metrics']['Net Credit Loss Coverage'].get(quarter)
                row_data[quarter] = clean_numeric_value(value)
            
            table_data.append(row_data)
    
    return pd.DataFrame(table_data)

def create_combined_tables_figure(coverage_df, ncl_coverage_df):
    """Create side-by-side tables in one figure"""
    
    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{"type": "table"}, {"type": "table"}]],
        subplot_titles=["Coverage Rates", "NCL Coverage"],
        horizontal_spacing=0.1
    )
    
    # Coverage rates table
    if not coverage_df.empty:
        coverage_headers = []
        coverage_values = []
        for col in coverage_df.columns:
            if col == 'Bank':
                coverage_headers.append('Coverage Rates')
            elif col == 'Δ Qtr (bps)':
                coverage_headers.append('Δ Q4\'24')
            else:
                coverage_headers.append(col)
            
            column_data = []
            for idx, row in coverage_df.iterrows():
                val = row[col]
                if col == 'Bank':
                    column_data.append(val)
                elif pd.isna(val):
                    column_data.append('-')
                elif 'bps' in col or 'Δ' in col:
                    column_data.append(f"{int(val)} bps" if not pd.isna(val) else '-')
                elif isinstance(val, float):
                    column_data.append(f"{val:.2f}%" if val < 100 else f"{val:.0f}")
                else:
                    column_data.append(str(val))
            coverage_values.append(column_data)
        
        fig.add_trace(
            go.Table(
                header=dict(values=coverage_headers, fill_color='lightblue', align='center', font=dict(size=11)),
                cells=dict(values=coverage_values, fill_color='white', align='center', font=dict(size=10))
            ),
            row=1, col=1
        )
    
    # NCL Coverage table
    if not ncl_coverage_df.empty:
        ncl_headers = []
        ncl_values = []
        for col in ncl_coverage_df.columns:
            if col == 'Bank':
                ncl_headers.append('NCL Coverage')
            else:
                ncl_headers.append(col)
            
            column_data = []
            for idx, row in ncl_coverage_df.iterrows():
                val = row[col]
                if col == 'Bank':
                    column_data.append(val)
                elif pd.isna(val):
                    column_data.append('-')
                elif isinstance(val, float):
                    column_data.append(f"{val:.2f}%" if val < 100 else f"{val:.0f}")
                else:
                    column_data.append(str(val))
            ncl_values.append(column_data)
        
        fig.add_trace(
            go.Table(
                header=dict(values=ncl_headers, fill_color='lightblue', align='center', font=dict(size=11)),
                cells=dict(values=ncl_values, fill_color='white', align='center', font=dict(size=10))
            ),
            row=1, col=2
        )
    
    # Calculate dynamic height based on number of rows
    max_rows = max(len(coverage_df) if not coverage_df.empty else 0, 
                   len(ncl_coverage_df) if not ncl_coverage_df.empty else 0)
    height = 250 + max_rows * 35
    
    fig.update_layout(
        title=dict(text="📊 Coverage Rates & NCL Coverage", font=dict(size=16), x=0.5),
        height=height,
        margin=dict(l=20, r=20, t=80, b=20)
    )
    
    return fig

def create_line_chart_with_table(banks_data, metric_name, metric_category, quarters, title, ylabel):
    """Create line chart with summary table using Plotly"""
    
    # Prepare chart data
    chart_data = {}
    for bank_name, bank_data in banks_data.items():
        if metric_category in bank_data and metric_name in bank_data[metric_category]:
            values = []
            for quarter in quarters:
                value = bank_data[metric_category][metric_name].get(quarter)
                values.append(clean_numeric_value(value))
            
            if any(not pd.isna(v) for v in values):  # Only include if has some data
                chart_data[bank_name] = values
    
    # Create subplot with chart and table
    fig = make_subplots(
        rows=1, cols=2,
        column_widths=[0.7, 0.3],
        specs=[[{"type": "scatter"}, {"type": "table"}]],
        subplot_titles=[title, "Last 2 Quarters Summary"]
    )
    
    # Add line chart
    color_idx = 0
    for bank_name, values in chart_data.items():
        color = BANK_COLORS.get(bank_name, PLOTLY_COLORS[color_idx % len(PLOTLY_COLORS)])
        color_idx += 1
        
        # Only plot non-NaN values
        valid_data = [(i, v) for i, v in enumerate(values) if not pd.isna(v)]
        if valid_data:
            x_vals, y_vals = zip(*valid_data)
            quarter_labels = [quarters[i] for i in x_vals]
            
            fig.add_trace(
                go.Scatter(
                    x=quarter_labels,
                    y=y_vals,
                    mode='lines+markers',
                    name=bank_name,
                    line=dict(color=color, width=3),
                    marker=dict(size=6, color=color),
                    hovertemplate=f'<b>{bank_name}</b><br>Quarter: %{{x}}<br>Rate: %{{y:.2f}}%<extra></extra>'
                ),
                row=1, col=1
            )
    
    # Create summary table data for last 2 quarters
    if len(quarters) >= 2:
        last_two_quarters = quarters[-2:]
        
        # Prepare table data
        table_headers = ['Bank', last_two_quarters[0], last_two_quarters[1], 'Change (bps)']
        table_values = [[], [], [], []]
        
        for bank_name, values in chart_data.items():
            table_values[0].append(bank_name)
            
            # Previous quarter value
            prev_idx = quarters.index(last_two_quarters[0])
            prev_val = values[prev_idx] if prev_idx < len(values) and not pd.isna(values[prev_idx]) else None
            
            # Latest quarter value
            latest_idx = quarters.index(last_two_quarters[1])
            latest_val = values[latest_idx] if latest_idx < len(values) and not pd.isna(values[latest_idx]) else None
            
            # Add values
            if prev_val is not None:
                table_values[1].append(f"{prev_val:.2f}%")
            else:
                table_values[1].append('-')
                
            if latest_val is not None:
                table_values[2].append(f"{latest_val:.2f}%")
            else:
                table_values[2].append('-')
            
            # Calculate change in basis points
            if prev_val is not None and latest_val is not None:
                change_bps = (latest_val - prev_val) * 100  # Convert to basis points
                table_values[3].append(f"{change_bps:+.0f} bps")
            else:
                table_values[3].append('-')
        
        # Add table to subplot
        fig.add_trace(
            go.Table(
                header=dict(
                    values=table_headers,
                    fill_color='lightblue',
                    align='center',
                    font=dict(size=10)
                ),
                cells=dict(
                    values=table_values,
                    fill_color='white',
                    align='center',
                    font=dict(size=9)
                )
            ),
            row=1, col=2
        )
    
    # Update layout
    fig.update_xaxes(title_text="Quarter", row=1, col=1)
    fig.update_yaxes(title_text=ylabel, row=1, col=1)
    
    fig.update_layout(
        height=450,  # Fixed height for consistency
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=0.7
        ),
        margin=dict(l=50, r=50, t=80, b=50)
    )
    
    return fig

class DashboardComponents:
    """Class to manage dashboard components and display options"""
    
    def __init__(self):
        self.components = []
        self.titles = []
    
    def add_component(self, figure, title):
        """Add a component to the dashboard"""
        self.components.append(figure)
        self.titles.append(title)
    
    def show_individual(self, component_index):
        """Show a specific component by index"""
        if 0 <= component_index < len(self.components):
            print(f"📊 Displaying: {self.titles[component_index]}")
            self.components[component_index].show()
        else:
            print(f"❌ Invalid component index. Available: 0-{len(self.components)-1}")
    
    def show_all_separate(self):
        """Show all components in separate browser tabs"""
        print(f"🌐 Opening {len(self.components)} components in separate tabs...")
        for i, (component, title) in enumerate(zip(self.components, self.titles)):
            print(f"  {i+1}. {title}")
            component.show()
    
    def list_components(self):
        """List all available components"""
        print("📋 Available Dashboard Components:")
        for i, title in enumerate(self.titles):
            print(f"  {i}: {title}")
    
    def save_html(self, filename="banking_dashboard_complete.html"):
        """Save all components to a single HTML file"""
        html_content = self._generate_html()
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        html_path = os.path.abspath(filename)
        print(f"💾 Dashboard saved: {html_path}")
        return html_path
    
    def save_and_open(self, filename="banking_dashboard_complete.html"):
        """Save to HTML and open in browser"""
        html_path = self.save_html(filename)
        webbrowser.open(f"file://{html_path}")
        print(f"🌐 Opening in browser: {html_path}")
        return html_path
    
    def _generate_html(self):
        """Generate complete HTML with all components"""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Banking Dashboard - Credit Risk Metrics</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    margin: 20px; 
                    background-color: #f8f9fa; 
                    line-height: 1.6;
                }
                .dashboard-title { 
                    text-align: center; 
                    color: #2c3e50; 
                    margin-bottom: 30px; 
                    padding: 20px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border-radius: 10px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                }
                .section { 
                    margin: 30px 0; 
                    padding: 20px; 
                    background-color: white; 
                    border-radius: 8px; 
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1); 
                }
                .chart-container { 
                    margin: 20px 0; 
                    border: 1px solid #e0e0e0;
                    border-radius: 8px;
                    padding: 10px;
                    background-color: #fafafa;
                }
                .component-title {
                    color: #34495e;
                    border-bottom: 2px solid #3498db;
                    padding-bottom: 10px;
                    margin-bottom: 20px;
                }
            </style>
        </head>
        <body>
            <h1 class="dashboard-title">🏦 Banking Dashboard - Credit Risk Metrics</h1>
        """
        
        # Add each component to HTML
        for i, (component, title) in enumerate(zip(self.components, self.titles)):
            html_content += f"""
            <div class="section">
                <h2 class="component-title">{title}</h2>
                <div class="chart-container" id="chart{i}"></div>
            </div>
            """
            
            # Add the Plotly JavaScript
            component_json = component.to_json()
            html_content += f"""
            <script>
                var plotlyDiv{i} = document.getElementById('chart{i}');
                var plotData{i} = {component_json};
                Plotly.newPlot(plotlyDiv{i}, plotData{i}.data, plotData{i}.layout, {{responsive: true}});
            </script>
            """
        
        html_content += """
            <div class="section">
                <p style="text-align: center; color: #7f8c8d; font-style: italic;">
                    Generated with Plotly • Interactive Dashboard • Hover for details
                </p>
            </div>
        </body>
        </html>
        """
        
        return html_content

def create_dashboard(json_file_path, display_mode="save_and_open"):
    """
    Create the complete dashboard
    
    display_mode options:
    - "save_and_open": Save HTML and open in browser (default)
    - "save_only": Save HTML file only
    - "individual": Show each component separately
    - "none": Don't display, just return components
    """
    
    # Load data
    banks_data = load_and_process_data(json_file_path)
    quarters = get_quarters_from_data(banks_data)
    
    print(f"🔍 Found quarters: {quarters}")
    print(f"🏦 Found banks: {list(banks_data.keys())}")
    
    # Initialize dashboard components manager
    dashboard = DashboardComponents()
    
    # 1. Create combined tables
    coverage_df = create_coverage_table_data(banks_data, quarters)
    ncl_coverage_df = create_ncl_coverage_table_data(banks_data, quarters)
    
    if not coverage_df.empty or not ncl_coverage_df.empty:
        tables_fig = create_combined_tables_figure(coverage_df, ncl_coverage_df)
        dashboard.add_component(tables_fig, "📊 Coverage Rates & NCL Coverage")
    
    # 2. NCL Rate Chart
    ncl_chart = create_line_chart_with_table(
        banks_data, 'Net Credit Loss Rate (%)', 'metrics', quarters,
        'NCL rates have increased in Q1\'25 in line with majority of the US peers',
        'NCL Rate (%)'
    )
    dashboard.add_component(ncl_chart, "📈 Net Credit Loss (NCL) Rates")
    
    # 3. 30+ Days Delinquency Chart
    dq30_chart = create_line_chart_with_table(
        banks_data, '30+ Delinquency Rate (%)', 'metrics', quarters,
        '30+ Days Delinquency rates trend',
        '30+ DQ Rate (%)'
    )
    dashboard.add_component(dq30_chart, "📊 30+ Days Delinquency Rates")
    
    # 4. 90+ Days Delinquency Chart
    dq90_chart = create_line_chart_with_table(
        banks_data, '90+ Delinquency Rate (%)', 'metrics', quarters,
        '90+ Days Delinquency rates trend',
        '90+ DQ Rate (%)'
    )
    dashboard.add_component(dq90_chart, "📉 90+ Days Delinquency Rates")
    
    # Display based on mode
    if display_mode == "save_and_open":
        dashboard.save_and_open()
    elif display_mode == "save_only":
        dashboard.save_html()
    elif display_mode == "individual":
        dashboard.show_all_separate()
    elif display_mode == "list":
        dashboard.list_components()
    
    print(f"\n✅ Dashboard created with {len(dashboard.components)} components")
    return dashboard

# Main execution
if __name__ == "__main__":
    base_dir = "D:/office_Work_shennanigans/hackathon/integrated_hackathon_codebase"
    json_file_path = os.path.join(base_dir, "results/Q12025/consolidated_results.json")
    
    try:
        # Create dashboard with different display options
        print("🚀 Creating Banking Dashboard...")
        
        # Option 1: Save and open in browser (recommended)
        dashboard = create_dashboard(json_file_path, display_mode="save_and_open")
        
        # Additional options you can use:
        print("\n🎯 Additional Display Options:")
        print("dashboard.list_components()           # List all components")
        print("dashboard.show_individual(0)         # Show first component only")
        print("dashboard.show_all_separate()        # Show all in separate tabs")
        print("dashboard.save_html('custom.html')   # Save with custom filename")
        
    except FileNotFoundError:
        print(f"❌ Error: File '{json_file_path}' not found.")
    except Exception as e:
        print(f"❌ An error occurred: {str(e)}")
        import traceback
        traceback.print_exc()