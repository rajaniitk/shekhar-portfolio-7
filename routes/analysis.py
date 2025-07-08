import logging
import traceback
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from models import Dataset, Analysis
from services.data_processor import DataProcessor
from services.eda_engine import EDAEngine
from services.insights_generator import InsightsGenerator
from app import db
from datetime import datetime
from models import ModelTraining

analysis_bp = Blueprint('analysis', __name__)

@analysis_bp.route('/comparison')
def comparison_page():
    """Data comparison analysis page"""
    try:
        datasets = Dataset.query.order_by(Dataset.upload_date.desc()).all()
        datasets_data = [dataset.to_dict() for dataset in datasets]
        return render_template('comparison.html', datasets=datasets_data)
    except Exception as e:
        logging.error(f"Comparison page error: {str(e)}")
        flash(f'Error loading comparison page: {str(e)}', 'error')
        return redirect(url_for('main.index'))

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

@analysis_bp.route('/api/compare', methods=['POST'])
def compare_datasets():
    """Compare two datasets using various analysis methods"""
    try:
        data = request.get_json()
        
        primary_dataset_id = data.get('primary_dataset_id')
        secondary_dataset_id = data.get('secondary_dataset_id')
        comparison_type = data.get('comparison_type', 'columns')
        column_mappings = data.get('column_mappings', [])
        options = data.get('options', {})
        
        if not primary_dataset_id or not secondary_dataset_id:
            return jsonify({'success': False, 'error': 'Both dataset IDs are required'}), 400
        
        # Get datasets
        primary_dataset = Dataset.query.get_or_404(primary_dataset_id)
        secondary_dataset = Dataset.query.get_or_404(secondary_dataset_id)
        
        # Load data
        processor = DataProcessor()
        primary_df, _ = processor.load_file(primary_dataset.file_path)
        secondary_df, _ = processor.load_file(secondary_dataset.file_path)
        
        if primary_df is None or secondary_df is None:
            return jsonify({'success': False, 'error': 'Could not load dataset files'}), 500
        
        # Perform comparison based on type
        comparison_results = {}
        
        if comparison_type == 'columns':
            comparison_results = perform_column_comparison(primary_df, secondary_df, primary_dataset, secondary_dataset)
        elif comparison_type == 'statistical':
            comparison_results = perform_statistical_comparison(primary_df, secondary_df, column_mappings)
        elif comparison_type == 'distribution':
            comparison_results = perform_distribution_comparison(primary_df, secondary_df, column_mappings)
        elif comparison_type == 'models':
            comparison_results = perform_model_comparison(primary_dataset_id, secondary_dataset_id)
        
        # Add visualizations if requested
        if options.get('include_visualizations', True):
            comparison_results['visualizations'] = generate_comparison_visualizations(
                primary_df, secondary_df, comparison_type, column_mappings
            )
        
        return jsonify({
            'success': True,
            'results': comparison_results,
            'metadata': {
                'primary_dataset': primary_dataset.to_dict(),
                'secondary_dataset': secondary_dataset.to_dict(),
                'comparison_type': comparison_type,
                'generated_at': datetime.utcnow().isoformat()
            }
        })
        
    except Exception as e:
        logging.error(f"Dataset comparison error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

def perform_column_comparison(primary_df, secondary_df, primary_dataset, secondary_dataset):
    """Perform column-wise comparison between datasets"""
    results = {
        'overview': {
            'primary': {
                'rows': len(primary_df),
                'columns': len(primary_df.columns),
                'memory_mb': primary_df.memory_usage(deep=True).sum() / 1024 / 1024,
                'missing_percentage': (primary_df.isnull().sum().sum() / (len(primary_df) * len(primary_df.columns))) * 100,
                'duplicates': primary_df.duplicated().sum()
            },
            'secondary': {
                'rows': len(secondary_df),
                'columns': len(secondary_df.columns),
                'memory_mb': secondary_df.memory_usage(deep=True).sum() / 1024 / 1024,
                'missing_percentage': (secondary_df.isnull().sum().sum() / (len(secondary_df) * len(secondary_df.columns))) * 100,
                'duplicates': secondary_df.duplicated().sum()
            }
        },
        'column_comparison': {},
        'common_columns': [],
        'unique_columns': {
            'primary': [],
            'secondary': []
        }
    }
    
    # Find common and unique columns
    primary_cols = set(primary_df.columns)
    secondary_cols = set(secondary_df.columns)
    
    results['common_columns'] = list(primary_cols.intersection(secondary_cols))
    results['unique_columns']['primary'] = list(primary_cols - secondary_cols)
    results['unique_columns']['secondary'] = list(secondary_cols - primary_cols)
    
    # Compare common columns
    for col in results['common_columns']:
        if col in primary_df.columns and col in secondary_df.columns:
            results['column_comparison'][col] = compare_single_column(primary_df[col], secondary_df[col])
    
    return results

def compare_single_column(primary_col, secondary_col):
    """Compare two columns and return comparison metrics"""
    comparison = {
        'data_types': {
            'primary': str(primary_col.dtype),
            'secondary': str(secondary_col.dtype),
            'compatible': str(primary_col.dtype) == str(secondary_col.dtype)
        },
        'basic_stats': {}
    }
    
    # Basic statistics comparison
    if primary_col.dtype in ['int64', 'float64'] and secondary_col.dtype in ['int64', 'float64']:
        comparison['basic_stats'] = {
            'primary': {
                'mean': float(primary_col.mean()) if not primary_col.empty else None,
                'median': float(primary_col.median()) if not primary_col.empty else None,
                'std': float(primary_col.std()) if not primary_col.empty else None,
                'min': float(primary_col.min()) if not primary_col.empty else None,
                'max': float(primary_col.max()) if not primary_col.empty else None
            },
            'secondary': {
                'mean': float(secondary_col.mean()) if not secondary_col.empty else None,
                'median': float(secondary_col.median()) if not secondary_col.empty else None,
                'std': float(secondary_col.std()) if not secondary_col.empty else None,
                'min': float(secondary_col.min()) if not secondary_col.empty else None,
                'max': float(secondary_col.max()) if not secondary_col.empty else None
            }
        }
    
    # Missing values comparison
    comparison['missing_values'] = {
        'primary': {
            'count': int(primary_col.isnull().sum()),
            'percentage': float((primary_col.isnull().sum() / len(primary_col)) * 100)
        },
        'secondary': {
            'count': int(secondary_col.isnull().sum()),
            'percentage': float((secondary_col.isnull().sum() / len(secondary_col)) * 100)
        }
    }
    
    # Unique values comparison
    comparison['unique_values'] = {
        'primary': int(primary_col.nunique()),
        'secondary': int(secondary_col.nunique())
    }
    
    return comparison

def perform_statistical_comparison(primary_df, secondary_df, column_mappings):
    """Perform statistical tests between datasets"""
    from scipy import stats
    import numpy as np
    
    results = {
        'tests_performed': [],
        'summary': {
            'total_tests': 0,
            'significant_results': 0,
            'confidence_level': 0.95
        }
    }
    
    # If no column mappings provided, compare common numeric columns
    if not column_mappings:
        common_numeric_cols = []
        for col in primary_df.columns:
            if (col in secondary_df.columns and 
                primary_df[col].dtype in ['int64', 'float64'] and 
                secondary_df[col].dtype in ['int64', 'float64']):
                common_numeric_cols.append(col)
                column_mappings.append({'primary': col, 'secondary': col})
    
    for mapping in column_mappings:
        primary_col = mapping['primary']
        secondary_col = mapping['secondary']
        
        if (primary_col in primary_df.columns and secondary_col in secondary_df.columns):
            primary_data = primary_df[primary_col].dropna()
            secondary_data = secondary_df[secondary_col].dropna()
            
            if len(primary_data) > 0 and len(secondary_data) > 0:
                # Perform various statistical tests
                test_results = {}
                
                # T-test (if both are numeric)
                if (primary_data.dtype in ['int64', 'float64'] and 
                    secondary_data.dtype in ['int64', 'float64']):
                    try:
                        t_stat, p_value = stats.ttest_ind(primary_data, secondary_data)
                        test_results['t_test'] = {
                            'statistic': float(t_stat),
                            'p_value': float(p_value),
                            'significant': p_value < 0.05,
                            'interpretation': 'Means are significantly different' if p_value < 0.05 else 'No significant difference in means'
                        }
                    except:
                        pass
                    
                    # Mann-Whitney U test
                    try:
                        u_stat, p_value = stats.mannwhitneyu(primary_data, secondary_data, alternative='two-sided')
                        test_results['mann_whitney'] = {
                            'statistic': float(u_stat),
                            'p_value': float(p_value),
                            'significant': p_value < 0.05,
                            'interpretation': 'Distributions are significantly different' if p_value < 0.05 else 'No significant difference in distributions'
                        }
                    except:
                        pass
                    
                    # Kolmogorov-Smirnov test
                    try:
                        ks_stat, p_value = stats.ks_2samp(primary_data, secondary_data)
                        test_results['kolmogorov_smirnov'] = {
                            'statistic': float(ks_stat),
                            'p_value': float(p_value),
                            'significant': p_value < 0.05,
                            'interpretation': 'Distributions are significantly different' if p_value < 0.05 else 'No significant difference in distributions'
                        }
                    except:
                        pass
                
                if test_results:
                    results['tests_performed'].append({
                        'columns': f"{primary_col} vs {secondary_col}",
                        'tests': test_results
                    })
                    
                    # Update summary
                    results['summary']['total_tests'] += len(test_results)
                    for test_name, test_result in test_results.items():
                        if test_result.get('significant', False):
                            results['summary']['significant_results'] += 1
    
    return results

def perform_distribution_comparison(primary_df, secondary_df, column_mappings):
    """Compare distributions between datasets"""
    results = {
        'distribution_metrics': {},
        'normality_tests': {},
        'summary': {}
    }
    
    # If no column mappings, use common numeric columns
    if not column_mappings:
        for col in primary_df.columns:
            if (col in secondary_df.columns and 
                primary_df[col].dtype in ['int64', 'float64'] and 
                secondary_df[col].dtype in ['int64', 'float64']):
                column_mappings.append({'primary': col, 'secondary': col})
    
    for mapping in column_mappings:
        primary_col = mapping['primary']
        secondary_col = mapping['secondary']
        
        if (primary_col in primary_df.columns and secondary_col in secondary_df.columns):
            primary_data = primary_df[primary_col].dropna()
            secondary_data = secondary_df[secondary_col].dropna()
            
            if (len(primary_data) > 0 and len(secondary_data) > 0 and
                primary_data.dtype in ['int64', 'float64'] and 
                secondary_data.dtype in ['int64', 'float64']):
                
                # Calculate distribution metrics
                results['distribution_metrics'][f"{primary_col}_vs_{secondary_col}"] = {
                    'primary': {
                        'mean': float(primary_data.mean()),
                        'median': float(primary_data.median()),
                        'std': float(primary_data.std()),
                        'skewness': float(primary_data.skew()),
                        'kurtosis': float(primary_data.kurtosis()),
                        'q25': float(primary_data.quantile(0.25)),
                        'q75': float(primary_data.quantile(0.75))
                    },
                    'secondary': {
                        'mean': float(secondary_data.mean()),
                        'median': float(secondary_data.median()),
                        'std': float(secondary_data.std()),
                        'skewness': float(secondary_data.skew()),
                        'kurtosis': float(secondary_data.kurtosis()),
                        'q25': float(secondary_data.quantile(0.25)),
                        'q75': float(secondary_data.quantile(0.75))
                    }
                }
    
    return results

def perform_model_comparison(primary_dataset_id, secondary_dataset_id):
    """Compare ML model performance between datasets"""
    results = {
        'models_compared': [],
        'performance_metrics': {},
        'summary': {}
    }
    
    # Get models for both datasets
    primary_models = ModelTraining.query.filter_by(dataset_id=primary_dataset_id).all()
    secondary_models = ModelTraining.query.filter_by(dataset_id=secondary_dataset_id).all()
    
    results['models_compared'] = {
        'primary_dataset_models': len(primary_models),
        'secondary_dataset_models': len(secondary_models)
    }
    
    # Compare model performance
    for primary_model in primary_models:
        primary_metrics = primary_model.get_performance_metrics()
        
        for secondary_model in secondary_models:
            if primary_model.model_type == secondary_model.model_type:
                secondary_metrics = secondary_model.get_performance_metrics()
                
                comparison_key = f"{primary_model.model_type}_{primary_model.id}_vs_{secondary_model.id}"
                results['performance_metrics'][comparison_key] = {
                    'model_type': primary_model.model_type,
                    'primary_performance': primary_metrics,
                    'secondary_performance': secondary_metrics
                }
    
    return results

def generate_comparison_visualizations(primary_df, secondary_df, comparison_type, column_mappings):
    """Generate visualizations for dataset comparison"""
    visualizations = {}
    
    try:
        from services.visualization_engine import VisualizationEngine
        viz_engine = VisualizationEngine()
        
        # Create comparison plots based on type
        if comparison_type == 'columns' and column_mappings:
            for mapping in column_mappings[:3]:  # Limit to first 3 mappings
                primary_col = mapping['primary']
                secondary_col = mapping['secondary']
                
                if (primary_col in primary_df.columns and secondary_col in secondary_df.columns):
                    # Create side-by-side comparison plots
                    comparison_data = {
                        'primary': primary_df[primary_col].dropna(),
                        'secondary': secondary_df[secondary_col].dropna()
                    }
                    
                    viz_key = f"comparison_{primary_col}_vs_{secondary_col}"
                    visualizations[viz_key] = {
                        'type': 'comparison_plot',
                        'data': comparison_data,
                        'title': f'Comparison: {primary_col} vs {secondary_col}'
                    }
        
        return visualizations
        
    except Exception as e:
        logging.warning(f"Could not generate comparison visualizations: {str(e)}")
        return {}
