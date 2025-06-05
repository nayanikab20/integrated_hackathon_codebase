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

def add_text_annotation(fig, text, x_position=0.5, y_position=-0.20, 
                       font_size=12, text_width=200, annotation_width=1500,
                       bottom_margin=90, with_background=False, 
                       bg_color="rgba(248, 249, 250, 0.9)", border_color="#e0e0e0"):
    """
    Add a text annotation below the existing figure content with proper text wrapping
    
    Parameters:
    - fig: Plotly figure object
    - text: Text to display
    - x_position: X position (0-1, where 0.5 is center)
    - y_position: Y position (negative values place it below the figure)
    - font_size: Font size for the text (default: 12)
    - text_width: Character width for text wrapping (default: 200)
    - annotation_width: Width of the annotation box in pixels (default: 1500)
    - bottom_margin: Bottom margin to add for the annotation (default: 90)
    - with_background: Whether to show background box (default: False)
    - bg_color: Background color if with_background=True
    - border_color: Border color if with_background=True
    """
    # Break long text into multiple lines for better readability
    import textwrap
    wrapped_text = "<br>".join(textwrap.wrap(text, width=text_width))
    
    # Build annotation parameters
    annotation_params = {
        'text': wrapped_text,
        'x': x_position,
        'y': y_position,
        'xref': "paper",
        'yref': "paper",
        'showarrow': False,
        'font': dict(size=font_size, color="#2c3e50"),
        'align': "center",
        'width': annotation_width,
        'xanchor': "center"
    }
    
    # Add background styling if requested
    if with_background:
        annotation_params.update({
            'bgcolor': bg_color,
            'bordercolor': border_color,
            'borderwidth': 1,
            'borderpad': 10
        })
    
    fig.add_annotation(**annotation_params)
    
    # Adjust the bottom margin to accommodate the annotation
    current_margin = fig.layout.margin
    fig.update_layout(
        margin=dict(
            l=current_margin.l if current_margin.l else 20,
            r=current_margin.r if current_margin.r else 20,
            t=current_margin.t if current_margin.t else 80,
            b=bottom_margin
        )
    )
    
    return fig

def add_download_button(fig, button_text="Download", x_position=0.95, y_position=0.95):
    """
    Add a download button to the figure that can save as PDF
    
    Parameters:
    - fig: Plotly figure object
    - button_text: Text to display on button
    - x_position: X position (0-1, where 0.95 is top-right)
    - y_position: Y position (0-1, where 0.95 is top-right)
    """
    
    # Add download button as an annotation with custom styling
    fig.add_annotation(
        text=f"📥 {button_text}",
        x=x_position,
        y=y_position,
        xref="paper",
        yref="paper",
        showarrow=False,
        font=dict(size=12, color="white", family="Arial, sans-serif"),
        align="center",
        bgcolor="#28a745",  # Bootstrap green color
        bordercolor="#1e7e34",  # Darker green border
        borderwidth=2,
        borderpad=8,
        xanchor="center",
        yanchor="middle",
        # Make it look like a button
        clicktoshow=False
    )
    
    # Add JavaScript for PDF download functionality
    fig.update_layout(
        annotations=fig.layout.annotations + (
            dict(
                text='<button onclick="downloadPDF()" style="background-color:#28a745; color:white; border:2px solid #1e7e34; padding:8px 16px; border-radius:4px; cursor:pointer; font-size:12px; font-family:Arial;">📥 Download</button>',
                x=x_position,
                y=y_position,
                xref="paper",
                yref="paper",
                showarrow=False,
                bgcolor="rgba(0,0,0,0)",  # Transparent background
                borderwidth=0
            ),
        )
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
        """Generate complete HTML with single top download button"""
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Banking Dashboard - Credit Risk Metrics</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    margin: 20px; 
                    background-color: #f8f9fa; 
                    line-height: 1.6;
                }
                .dashboard-header {
                    position: relative;
                    margin-bottom: 30px;
                }
                .dashboard-title { 
                    text-align: center; 
                    color: #2c3e50; 
                    padding: 20px;
                    background: #00aeef;
                    color: white;
                    border-radius: 10px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                    margin: 0;
                }
                .download-btn {
                    position: absolute;
                    top: 20px;
                    right: 20px;
                    background-color: #28a745;
                    color: white;
                    border: 2px solid #1e7e34;
                    padding: 10px 20px;
                    border-radius: 6px;
                    cursor: pointer;
                    font-size: 14px;
                    font-family: Arial, sans-serif;
                    font-weight: bold;
                    z-index: 1000;
                    transition: background-color 0.3s;
                }
                .download-btn:hover {
                    background-color: #218838;
                    transform: translateY(-1px);
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
                    color: #00aeef;
                    border-bottom: 2px solid #3498db;
                    padding-bottom: 10px;
                    margin-bottom: 20px;
                }
                @media print {
                    .download-btn { display: none; }
                }
            </style>
        </head>
        <body>
            <div id="dashboard-content">
                <div class="dashboard-header">
                    <h1 class="dashboard-title">🏦 Competitor Analysis Dashboard</h1>
                    <button class="download-btn" onclick="downloadDashboardPDF()">📥 Download</button>
                </div>
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
            </div>
            
            <script>
                // Download entire dashboard as PDF
                function downloadDashboardPDF() {
                    const element = document.getElementById('dashboard-content');
                    const opt = {
                        margin: 0.5,
                        filename: 'banking_dashboard_analysis.pdf',
                        image: { type: 'jpeg', quality: 0.98 },
                        html2canvas: { 
                            scale: 2, 
                            useCORS: true,
                            logging: false,
                            allowTaint: true
                        },
                        jsPDF: { unit: 'in', format: 'a4', orientation: 'landscape' },
                        pagebreak: { mode: ['avoid-all', 'css', 'legacy'] }
                    };
                    
                    // Show loading state
                    const btn = document.querySelector('.download-btn');
                    const originalText = btn.innerHTML;
                    btn.innerHTML = '⏳ Generating...';
                    btn.disabled = true;
                    
                    html2pdf().set(opt).from(element).save().then(function() {
                        // Reset button
                        btn.innerHTML = originalText;
                        btn.disabled = false;
                    });
                }
            </script>
            
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

    ncl_commentary = ("Coverage rates increased across all major banks in Q1 2025, reflecting heightened credit risk management amid economic uncertainty. Synchrony led with the most significant increase of 49 basis points to 11.78% followed by JPMorgan's 44 basis point rise to 6.71%. WellsFargo and Bank of America posted more modest increases of 25 and 19 basis points respectively.")
    
    if not coverage_df.empty or not ncl_coverage_df.empty:
        # Add the annotation paragraph
        tables_fig = create_combined_tables_figure(coverage_df, ncl_coverage_df)

        tables_fig = add_text_annotation(
            tables_fig, 
            ncl_commentary,
            y_position=-0.20,
            font_size=12,
            text_width=200,
            annotation_width=1500,
            with_background=False
        )
    dashboard.add_component(tables_fig, "📊 Coverage Rates & NCL Coverage")
    
    # 2. NCL Rate Chart
    ncl_chart = create_line_chart_with_table(
        banks_data, 'Net Credit Loss Rate (%)', 'metrics', quarters,
        'NCL rates have increased in Q1\'25 in line with majority of the US peers',
        'NCL Rate (%)'
    )

    # Add commentary specifically under the right-side table
    ncl_commentary = ("NCL rates show divergent trends in Q1 2025. Synchrony declined 7 bps to 6.38%, "
                    "while JPMorgan, WellsFargo, and Bank of America increased by 28, 27, and 26 bps respectively.")

    ncl_chart = add_text_annotation(
        ncl_chart, 
        ncl_commentary,
        x_position=0.85,      # Position over the right table (center of 0.7-1.0 range)
        y_position=-0.15,     # Position below the table
        font_size=12,         # Smaller font for table area
        text_width=60,        # Shorter line width for narrow table area
        annotation_width=400, # Smaller annotation width to fit table area
        bottom_margin=100,    # Increase margin for the annotation
        # with_background=True, # Add background for better readability
        bg_color="rgba(240, 248, 255, 0.9)",  # Light blue background
        border_color="#d0d0d0"
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