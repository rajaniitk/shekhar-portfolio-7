import logging
from flask import Blueprint, render_template, request, jsonify, current_app
from models import Dataset
from services.data_processor import DataProcessor
from services.visualization_engine import VisualizationEngine

visualization_bp = Blueprint('visualization', __name__)

def _handle_visualization_response(viz_result):
    """Helper function to handle visualization engine responses"""
    try:
        if isinstance(viz_result, dict):
            if 'error' in viz_result:
                return viz_result
            elif 'plot' in viz_result:
                return viz_result
            elif 'plots' in viz_result:
                return viz_result
            else:
                # If it's a dict but doesn't have expected keys, assume it's a plotly JSON
                return {'plot': viz_result, 'type': 'plotly'}
        elif isinstance(viz_result, str):
            # Legacy format - assume it's a plotly JSON string
            return {'plot': viz_result, 'type': 'plotly'}
        else:
            return {'error': 'Invalid visualization result format'}
    except Exception as e:
        logging.error(f"Error handling visualization response: {str(e)}")
        return {'error': f'Response handling error: {str(e)}'}

@visualization_bp.route('/<int:dataset_id>')
def visualization_page(dataset_id):
    """Visualization dashboard page"""
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        processor = DataProcessor()
        df, _ = processor.load_file(dataset.file_path)
        
        if df is not None:
            # Get column information for visualization options
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
            all_cols = list(df.columns)
            
            return render_template('visualization_dashboard.html', 
                                 dataset=dataset.to_dict(),
                                 numeric_columns=numeric_cols,
                                 categorical_columns=categorical_cols,
                                 all_columns=all_cols)
    except Exception as e:
        logging.error(f"Visualization page error: {str(e)}")
        current_app.logger.error(f"Visualization page error: {str(e)}")
    
    return render_template('visualization_dashboard.html', dataset={'id': dataset_id, 'name': 'Unknown'})

@visualization_bp.route('/api/generate/<int:dataset_id>')
def generate_visualizations(dataset_id):
    """Generate visualizations for dataset"""
    try:
        chart_types = request.args.getlist('charts')
        columns = request.args.getlist('columns')
        
        if not chart_types:
            return jsonify({'error': 'No chart types specified', 'success': False}), 400
        
        dataset = Dataset.query.get_or_404(dataset_id)
        processor = DataProcessor()
        df, _ = processor.load_file(dataset.file_path)
        
        if df is None:
            return jsonify({'error': 'Could not load dataset', 'success': False}), 500
        
        viz_engine = VisualizationEngine()
        visualizations = {}
        
        # Generate requested visualizations
        for chart_type in chart_types:
            try:
                if chart_type == 'correlation_heatmap':
                    result = viz_engine.create_correlation_heatmap(df)
                    visualizations['correlation_heatmap'] = _handle_visualization_response(result)
                    
                elif chart_type == 'distribution_plots' and columns:
                    visualizations['distribution_plots'] = {}
                    for col in columns:
                        if col in df.columns:
                            result = viz_engine.create_distribution_plot(df, col)
                            visualizations['distribution_plots'][col] = _handle_visualization_response(result)
                            
                elif chart_type == 'box_plots' and columns:
                    visualizations['box_plots'] = {}
                    for col in columns:
                        if col in df.columns:
                            result = viz_engine.create_box_plot(df, col)
                            visualizations['box_plots'][col] = _handle_visualization_response(result)
                            
                elif chart_type == 'scatter_matrix':
                    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                    if len(numeric_cols) >= 2:
                        result = viz_engine.create_scatter_matrix(df, numeric_cols[:10])
                        visualizations['scatter_matrix'] = _handle_visualization_response(result)
                    else:
                        visualizations['scatter_matrix'] = {'error': 'Insufficient numeric columns for scatter matrix'}
                        
                elif chart_type == 'pairplot':
                    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                    if len(numeric_cols) >= 2:
                        result = viz_engine.create_pairplot(df, numeric_cols[:8])
                        visualizations['pairplot'] = _handle_visualization_response(result)
                    else:
                        visualizations['pairplot'] = {'error': 'Insufficient numeric columns for pairplot'}
                        
                elif chart_type == 'violin_plots' and columns:
                    visualizations['violin_plots'] = {}
                    for col in columns:
                        if col in df.columns:
                            result = viz_engine.create_violin_plot(df, col)
                            visualizations['violin_plots'][col] = _handle_visualization_response(result)
                            
                elif chart_type == 'qq_plots' and columns:
                    visualizations['qq_plots'] = {}
                    for col in columns:
                        if col in df.columns and df[col].dtype in ['int64', 'float64']:
                            result = viz_engine.create_qq_plot(df, col)
                            visualizations['qq_plots'][col] = _handle_visualization_response(result)
                            
                elif chart_type == 'bar_charts' and columns:
                    visualizations['bar_charts'] = {}
                    for col in columns:
                        if col in df.columns:
                            result = viz_engine.create_bar_chart(df, col)
                            visualizations['bar_charts'][col] = _handle_visualization_response(result)
                            
                elif chart_type == 'pie_charts' and columns:
                    visualizations['pie_charts'] = {}
                    for col in columns:
                        if col in df.columns:
                            result = viz_engine.create_pie_chart(df, col)
                            visualizations['pie_charts'][col] = _handle_visualization_response(result)
                            
                elif chart_type == 'heatmaps':
                    result = viz_engine.create_comprehensive_heatmaps(df)
                    visualizations['heatmaps'] = _handle_visualization_response(result)
                    
                elif chart_type == '3d_plots':
                    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                    if len(numeric_cols) >= 3:
                        result = viz_engine.create_3d_plots(df, numeric_cols[:3])
                        visualizations['3d_plots'] = _handle_visualization_response(result)
                    else:
                        visualizations['3d_plots'] = {'error': 'Insufficient numeric columns for 3D plots'}
                        
                # Add univariate, bivariate, and multivariate analysis options
                elif chart_type == 'univariate_analysis' and columns:
                    visualizations['univariate_analysis'] = {}
                    for col in columns:
                        if col in df.columns:
                            # Create comprehensive univariate analysis
                            if df[col].dtype in ['int64', 'float64']:
                                result = viz_engine.create_distribution_plot(df, col)
                            else:
                                result = viz_engine.create_bar_chart(df, col)
                            visualizations['univariate_analysis'][col] = _handle_visualization_response(result)
                            
                elif chart_type == 'bivariate_analysis' and len(columns) >= 2:
                    visualizations['bivariate_analysis'] = {}
                    # Create scatter plots for all pairs
                    for i in range(len(columns)-1):
                        for j in range(i+1, len(columns)):
                            col1, col2 = columns[i], columns[j]
                            if col1 in df.columns and col2 in df.columns:
                                pair_key = f"{col1}_vs_{col2}"
                                result = viz_engine.create_comparison_visualizations(df, col1, col2)
                                visualizations['bivariate_analysis'][pair_key] = _handle_visualization_response(result)
                                
                elif chart_type == 'multivariate_analysis':
                    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
                    if len(numeric_cols) >= 3:
                        visualizations['multivariate_analysis'] = {}
                        # PCA visualization
                        result = viz_engine.create_pca_visualizations(df)
                        visualizations['multivariate_analysis']['pca'] = _handle_visualization_response(result)
                        # Correlation heatmap
                        result = viz_engine.create_correlation_heatmap(df)
                        visualizations['multivariate_analysis']['correlation'] = _handle_visualization_response(result)
                    else:
                        visualizations['multivariate_analysis'] = {'error': 'Insufficient numeric columns for multivariate analysis'}
                        
                else:
                    visualizations[chart_type] = {'error': f'Unknown chart type: {chart_type}'}
                    
            except Exception as chart_error:
                logging.error(f"Error generating {chart_type}: {str(chart_error)}")
                visualizations[chart_type] = {'error': str(chart_error)}
        
        return jsonify({'visualizations': visualizations, 'success': True})
        
    except Exception as e:
        logging.error(f"Visualization generation error: {str(e)}")
        current_app.logger.error(f"Visualization generation error: {str(e)}")
        return jsonify({'error': str(e), 'success': False}), 500

@visualization_bp.route('/api/comparison/<int:dataset_id>')
def comparison_visualizations(dataset_id):
    """Generate comparison visualizations between columns"""
    try:
        col1 = request.args.get('col1')
        col2 = request.args.get('col2')
        
        if not col1 or not col2:
            return jsonify({'error': 'Two columns must be specified'}), 400
        
        dataset = Dataset.query.get_or_404(dataset_id)
        processor = DataProcessor()
        df, _ = processor.load_file(dataset.file_path)
        
        if df is None:
            return jsonify({'error': 'Could not load dataset'}), 500
        
        if col1 not in df.columns or col2 not in df.columns:
            return jsonify({'error': 'One or both specified columns not found'}), 400
        
        viz_engine = VisualizationEngine()
        comparison_viz = viz_engine.create_comparison_visualizations(df, col1, col2)
        
        return jsonify(_handle_visualization_response(comparison_viz))
        
    except Exception as e:
        logging.error(f"Comparison visualization error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@visualization_bp.route('/api/advanced/<int:dataset_id>')
def advanced_visualizations(dataset_id):
    """Generate advanced visualizations"""
    try:
        viz_type = request.args.get('type')
        
        if not viz_type:
            return jsonify({'error': 'Visualization type must be specified'}), 400
        
        dataset = Dataset.query.get_or_404(dataset_id)
        processor = DataProcessor()
        df, _ = processor.load_file(dataset.file_path)
        
        if df is None:
            return jsonify({'error': 'Could not load dataset'}), 500
        
        viz_engine = VisualizationEngine()
        
        if viz_type == 'cluster_analysis':
            result = viz_engine.create_cluster_visualizations(df)
        elif viz_type == 'pca_analysis':
            result = viz_engine.create_pca_visualizations(df)
        elif viz_type == 'time_series':
            result = viz_engine.create_time_series_visualizations(df)
        elif viz_type == 'outlier_analysis':
            result = viz_engine.create_outlier_visualizations(df)
        elif viz_type == 'feature_importance':
            result = viz_engine.create_feature_importance_plots(df)
        else:
            return jsonify({'error': f'Unknown visualization type: {viz_type}'}), 400
        
        return jsonify(_handle_visualization_response(result))
        
    except Exception as e:
        logging.error(f"Advanced visualization error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@visualization_bp.route('/api/data/<int:dataset_id>')
def get_data_preview(dataset_id):
    """Get data preview for visualization"""
    try:
        page = int(request.args.get('page', 0))
        page_size = int(request.args.get('size', 100))
        
        dataset = Dataset.query.get_or_404(dataset_id)
        processor = DataProcessor()
        df, _ = processor.load_file(dataset.file_path)
        
        if df is None:
            return jsonify({'error': 'Could not load dataset', 'success': False}), 500
        
        # Calculate pagination
        total_rows = len(df)
        start_idx = page * page_size
        end_idx = min(start_idx + page_size, total_rows)
        
        # Get paginated data
        page_data = df.iloc[start_idx:end_idx]
        
        # Convert to list format for JSON
        data_list = []
        for _, row in page_data.iterrows():
            data_list.append([str(val) if val is not None else None for val in row.values])
        
        pagination_info = {
            'current_page': page,
            'page_size': page_size,
            'total_rows': total_rows,
            'total_pages': (total_rows + page_size - 1) // page_size,
            'start': start_idx,
            'end': end_idx
        }
        
        return jsonify({
            'data': data_list,
            'columns': list(df.columns),
            'pagination': pagination_info,
            'success': True
        })
        
    except Exception as e:
        logging.error(f"Data preview error: {str(e)}")
        return jsonify({'error': str(e), 'success': False}), 500

@visualization_bp.route('/api/custom/<int:dataset_id>', methods=['POST'])
def create_custom_chart(dataset_id):
    """Create custom chart based on user configuration"""
    try:
        chart_config = request.get_json()
        
        if not chart_config:
            return jsonify({'error': 'Chart configuration not provided', 'success': False}), 400
        
        dataset = Dataset.query.get_or_404(dataset_id)
        processor = DataProcessor()
        df, _ = processor.load_file(dataset.file_path)
        
        if df is None:
            return jsonify({'error': 'Could not load dataset', 'success': False}), 500
        
        viz_engine = VisualizationEngine()
        
        # Extract configuration
        chart_type = chart_config.get('chart_type')
        x_column = chart_config.get('x_column')
        y_column = chart_config.get('y_column')
        color_column = chart_config.get('color_column')
        size_column = chart_config.get('size_column')
        title = chart_config.get('title', f'{chart_type.title()} Chart')
        
        # Validate columns exist
        if x_column and x_column not in df.columns:
            return jsonify({'error': f'Column {x_column} not found', 'success': False}), 400
        
        if y_column and y_column not in df.columns:
            return jsonify({'error': f'Column {y_column} not found', 'success': False}), 400
        
        # Generate custom chart based on type
        try:
            if chart_type == 'scatter':
                if not y_column:
                    return jsonify({'error': 'Y column required for scatter plot', 'success': False}), 400
                result = viz_engine.create_scatter_plot(df, x_column, y_column, color_column, size_column, title)
                
            elif chart_type == 'line':
                if not y_column:
                    return jsonify({'error': 'Y column required for line chart', 'success': False}), 400
                result = viz_engine.create_line_chart(df, x_column, y_column, color_column, title)
                
            elif chart_type == 'bar':
                result = viz_engine.create_bar_chart(df, x_column, y_column, title)
                
            elif chart_type == 'histogram':
                result = viz_engine.create_distribution_plot(df, x_column)
                
            elif chart_type == 'box_plot':
                result = viz_engine.create_box_plot(df, x_column, y_column)
                
            elif chart_type == 'violin_plot':
                result = viz_engine.create_violin_plot(df, x_column, y_column)
                
            elif chart_type == 'heatmap':
                if df.select_dtypes(include=['number']).shape[1] < 2:
                    return jsonify({'error': 'Insufficient numeric columns for heatmap', 'success': False}), 400
                result = viz_engine.create_correlation_heatmap(df)
                
            elif chart_type == 'bubble':
                if not y_column or not size_column:
                    return jsonify({'error': 'Y column and size column required for bubble chart', 'success': False}), 400
                result = viz_engine.create_bubble_chart(df, x_column, y_column, size_column, color_column, title)
                
            else:
                return jsonify({'error': f'Unknown chart type: {chart_type}', 'success': False}), 400
            
            return jsonify({
                'chart': _handle_visualization_response(result),
                'config': chart_config,
                'success': True
            })
            
        except Exception as chart_error:
            return jsonify({'error': f'Chart generation error: {str(chart_error)}', 'success': False}), 500
        
    except Exception as e:
        logging.error(f"Custom chart creation error: {str(e)}")
        return jsonify({'error': str(e), 'success': False}), 500
