import logging
import traceback
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from models import Dataset, Analysis
from services.data_processor import DataProcessor
from services.eda_engine import EDAEngine
from services.insights_generator import InsightsGenerator
from app import db

analysis_bp = Blueprint('analysis', __name__)

@analysis_bp.route('/dataset/<int:dataset_id>')
def dataset_overview(dataset_id):
    """Dataset overview and basic EDA"""
    dataset = Dataset.query.get_or_404(dataset_id)
    
    try:
        # Debug : Check the dataset object
        print(f"DEBUG raw dataset object:- upload_date_type: {type(dataset.upload_date)}")
        print(f"DEBUG raw dataset object:- upload_date_value: {dataset.upload_date}")

        # DEBUG: Check the dict conversion
        dataset_dict = dataset.to_dict()
        print(f"DEBUG upload_date_type: {type(dataset_dict['upload_date'])}")
        print(f"DEBUG upload_date_value: {dataset_dict['upload_date']}")


        processor = DataProcessor()
        df, _ = processor.load_file(dataset.file_path)
        
        if df is not None:
            eda_engine = EDAEngine()
            basic_stats = eda_engine.generate_basic_statistics(df)

            print(f"DEBUG about to render template with dataset dict type: {type(dataset_dict)}")
            print(f"DEBUG dataset dict keys: {dataset_dict.keys()}")
            
            return render_template('analysis_dashboard.html', 
                                 dataset=dataset_dict,
                                 basic_stats=basic_stats,
                                 columns=list(df.columns))
    except Exception as e:
        logging.error(f"Dataset overview error: {str(e)}")
        logging.error(f"Error Type: {type(e).__name__}")
        logging.error(f"Traceback: {traceback.format_exc()}")
        flash(f'Error loading dataset: {str(e)}', 'error')
    
    return redirect(url_for('main.index'))

@analysis_bp.route('/column/<int:dataset_id>')
def column_analysis_page(dataset_id):
    """Column-wise analysis page"""
    dataset = Dataset.query.get_or_404(dataset_id)
    
    try:
        processor = DataProcessor()
        df, _ = processor.load_file(dataset.file_path)
        
        if df is not None:
            columns_info = {}
            for col in df.columns:
                columns_info[col] = {
                    'dtype': str(df[col].dtype),
                    'unique_count': df[col].nunique(),
                    'missing_count': df[col].isnull().sum(),
                    'missing_percentage': round((df[col].isnull().sum() / len(df)) * 100, 2)
                }
            
            return render_template('column_analysis.html', 
                                 dataset=dataset.to_dict(),
                                 columns_info=columns_info)
    except Exception as e:
        logging.error(f"Column analysis page error: {str(e)}")
        flash(f'Error loading column analysis: {str(e)}', 'error')
    
    return redirect(url_for('main.index'))

@analysis_bp.route('/api/eda/<int:dataset_id>')
def generate_eda(dataset_id):
    """Generate comprehensive EDA report"""
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        processor = DataProcessor()
        df, _ = processor.load_file(dataset.file_path)
        
        if df is not None:
            eda_engine = EDAEngine()
            
            # Generate comprehensive EDA
            eda_results = {
                'basic_stats': eda_engine.generate_basic_statistics(df),
                'missing_values': eda_engine.analyze_missing_values(df),
                'correlation_analysis': eda_engine.correlation_analysis(df),
                'outlier_detection': eda_engine.detect_outliers(df),
                'distribution_analysis': eda_engine.analyze_distributions(df),
                'duplicate_analysis': eda_engine.analyze_duplicates(df)
            }
            
            # Save analysis to database
            analysis = Analysis(
                dataset_id=dataset_id,
                analysis_type='comprehensive_eda'
            )
            analysis.set_results(eda_results)
            db.session.add(analysis)
            db.session.commit()
            
            return jsonify(eda_results)
            
    except Exception as e:
        logging.error(f"EDA generation error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@analysis_bp.route('/api/column_analysis/<int:dataset_id>')
def analyze_column(dataset_id):
    """Analyze specific columns"""
    try:
        columns = request.args.getlist('columns')
        if not columns:
            return jsonify({'error': 'No columns specified'}), 400
        
        dataset = Dataset.query.get_or_404(dataset_id)
        processor = DataProcessor()
        df, _ = processor.load_file(dataset.file_path)
        
        if df is not None:
            eda_engine = EDAEngine()
            insights_generator = InsightsGenerator()
            
            results = {}
            for column in columns:
                if column in df.columns:
                    column_analysis = eda_engine.analyze_single_column(df, column)
                    insights = insights_generator.generate_column_insights(df, column)
                    
                    results[column] = {
                        'analysis': column_analysis,
                        'insights': insights
                    }
            
            return jsonify(results)
            
    except Exception as e:
        logging.error(f"Column analysis error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@analysis_bp.route('/api/insights/<int:dataset_id>')
def generate_insights(dataset_id):
    """Generate AI-powered insights"""
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        processor = DataProcessor()
        df, _ = processor.load_file(dataset.file_path)
        
        if df is not None:
            insights_generator = InsightsGenerator()
            insights = insights_generator.generate_comprehensive_insights(df)
            
            # Save insights as analysis
            analysis = Analysis(
                dataset_id=dataset_id,
                analysis_type='ai_insights'
            )
            analysis.set_results(insights)
            db.session.add(analysis)
            db.session.commit()
            
            return jsonify(insights)
            
    except Exception as e:
        logging.error(f"Insights generation error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@analysis_bp.route('/api/column_details/<int:dataset_id>')
def get_column_details(dataset_id):
    """Get detailed statistics for all columns"""
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        processor = DataProcessor()
        df, _ = processor.load_file(dataset.file_path)
        
        if df is None:
            return jsonify({'error': 'Could not load dataset', 'success': False}), 500
        
        column_details = {}
        
        for col in df.columns:
            col_info = {
                'column_name': col,
                'data_type': str(df[col].dtype),
                'total_count': len(df),
                'non_null_count': int(df[col].count()),
                'null_count': int(df[col].isnull().sum()),
                'null_percentage': float((df[col].isnull().sum() / len(df)) * 100),
                'unique_count': int(df[col].nunique()),
                'unique_percentage': float((df[col].nunique() / len(df)) * 100)
            }
            
            # Add numeric statistics
            if df[col].dtype in ['int64', 'float64']:
                col_data = df[col].dropna()
                if len(col_data) > 0:
                    col_info.update({
                        'min': float(col_data.min()),
                        'max': float(col_data.max()),
                        'mean': float(col_data.mean()),
                        'median': float(col_data.median()),
                        'std': float(col_data.std()),
                        'variance': float(col_data.var()),
                        'q25': float(col_data.quantile(0.25)),
                        'q75': float(col_data.quantile(0.75)),
                        'iqr': float(col_data.quantile(0.75) - col_data.quantile(0.25)),
                        'range': float(col_data.max() - col_data.min()),
                        'skewness': float(col_data.skew()),
                        'kurtosis': float(col_data.kurtosis()),
                        'coefficient_of_variation': float(col_data.std() / col_data.mean()) if col_data.mean() != 0 else None,
                        'zeros_count': int((col_data == 0).sum()),
                        'negative_count': int((col_data < 0).sum()),
                        'positive_count': int((col_data > 0).sum())
                    })
                    
                    # Outlier detection using IQR method
                    Q1 = col_data.quantile(0.25)
                    Q3 = col_data.quantile(0.75)
                    IQR = Q3 - Q1
                    lower_bound = Q1 - 1.5 * IQR
                    upper_bound = Q3 + 1.5 * IQR
                    outliers = col_data[(col_data < lower_bound) | (col_data > upper_bound)]
                    
                    col_info.update({
                        'outliers_count': len(outliers),
                        'outliers_percentage': float((len(outliers) / len(col_data)) * 100),
                        'outlier_lower_bound': float(lower_bound),
                        'outlier_upper_bound': float(upper_bound)
                    })
            
            # Add categorical statistics
            elif df[col].dtype in ['object', 'category']:
                value_counts = df[col].value_counts()
                col_info.update({
                    'most_frequent': str(value_counts.index[0]) if len(value_counts) > 0 else None,
                    'most_frequent_count': int(value_counts.iloc[0]) if len(value_counts) > 0 else 0,
                    'most_frequent_percentage': float((value_counts.iloc[0] / len(df)) * 100) if len(value_counts) > 0 else 0,
                    'least_frequent': str(value_counts.index[-1]) if len(value_counts) > 0 else None,
                    'least_frequent_count': int(value_counts.iloc[-1]) if len(value_counts) > 0 else 0,
                    'cardinality': int(df[col].nunique()),
                    'top_5_values': dict(value_counts.head(5))
                })
                
                # Text analysis for string columns
                if df[col].dtype == 'object':
                    text_data = df[col].dropna().astype(str)
                    if len(text_data) > 0:
                        col_info.update({
                            'avg_length': float(text_data.str.len().mean()),
                            'min_length': int(text_data.str.len().min()),
                            'max_length': int(text_data.str.len().max()),
                            'total_characters': int(text_data.str.len().sum()),
                            'empty_strings': int((text_data == '').sum()),
                            'contains_numbers': int(text_data.str.contains(r'\d', na=False).sum()),
                            'contains_special_chars': int(text_data.str.contains(r'[^a-zA-Z0-9\s]', na=False).sum())
                        })
            
            column_details[col] = col_info
        
        return jsonify({
            'column_details': column_details,
            'dataset_shape': df.shape,
            'total_memory_usage': float(df.memory_usage(deep=True).sum() / 1024 / 1024),  # MB
            'success': True
        })
        
    except Exception as e:
        logging.error(f"Column details error: {str(e)}")
        return jsonify({'error': str(e), 'success': False}), 500

@analysis_bp.route('/api/column_action/<int:dataset_id>')
def column_action(dataset_id):
    """Perform actions on specific columns"""
    try:
        action = request.args.get('action')
        columns = request.args.getlist('columns')
        
        if not action or not columns:
            return jsonify({'error': 'Action and columns must be specified', 'success': False}), 400
        
        dataset = Dataset.query.get_or_404(dataset_id)
        processor = DataProcessor()
        df, _ = processor.load_file(dataset.file_path)
        
        if df is None:
            return jsonify({'error': 'Could not load dataset', 'success': False}), 500
        
        eda_engine = EDAEngine()
        insights_generator = InsightsGenerator()
        
        results = {}
        
        for column in columns:
            if column not in df.columns:
                results[column] = {'error': f'Column {column} not found'}
                continue
                
            try:
                if action == 'analyze':
                    column_analysis = eda_engine.analyze_single_column(df, column)
                    insights = insights_generator.generate_column_insights(df, column)
                    
                    results[column] = {
                        'analysis': column_analysis,
                        'insights': insights,
                        'success': True
                    }
                    
                elif action == 'describe':
                    if df[column].dtype in ['int64', 'float64']:
                        description = df[column].describe().to_dict()
                    else:
                        description = {
                            'count': len(df[column]),
                            'unique': df[column].nunique(),
                            'top': df[column].mode().iloc[0] if len(df[column].mode()) > 0 else None,
                            'freq': df[column].value_counts().iloc[0] if len(df[column]) > 0 else 0
                        }
                    results[column] = {'description': description, 'success': True}
                    
                elif action == 'value_counts':
                    value_counts = df[column].value_counts().head(20).to_dict()
                    results[column] = {'value_counts': value_counts, 'success': True}
                    
                elif action == 'missing_analysis':
                    missing_count = df[column].isnull().sum()
                    missing_percentage = (missing_count / len(df)) * 100
                    results[column] = {
                        'missing_count': int(missing_count),
                        'missing_percentage': float(missing_percentage),
                        'total_count': len(df),
                        'success': True
                    }
                    
                else:
                    results[column] = {'error': f'Unknown action: {action}', 'success': False}
                    
            except Exception as col_error:
                results[column] = {'error': str(col_error), 'success': False}
        
        return jsonify({'results': results, 'success': True})
        
    except Exception as e:
        logging.error(f"Column action error: {str(e)}")
        return jsonify({'error': str(e), 'success': False}), 500
