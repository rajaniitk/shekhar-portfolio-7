import logging
import json
import tempfile
import os
import pandas as pd
from datetime import datetime
from models import Dataset, Analysis, ModelTraining
from services.data_processor import DataProcessor
from services.eda_engine import EDAEngine
from services.statistical_tests import StatisticalTestEngine
from services.visualization_engine import VisualizationEngine
# For now, just save as JSON and return the path
# In production, this would generate an actual PDF


class ReportGenerator:
    """Service for generating comprehensive reports"""
    
    def __init__(self):
        self.data_processor = DataProcessor()
        self.eda_engine = EDAEngine()
        self.stats_engine = StatisticalTestEngine()
        self.viz_engine = VisualizationEngine()
    
    def generate_comprehensive_report(self, dataset_id):
        """Generate a comprehensive analysis report for a dataset"""
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            
            # Load dataset
            df, _ = self.data_processor.load_file(dataset.file_path)
            if df is None:
                return {'error': 'Could not load dataset'}
            
            report = {
                'dataset_info': dataset.to_dict(),
                'generated_at': datetime.now().isoformat(),
                'summary': {},
                'eda_results': {},
                'statistical_tests': {},
                'visualizations': {},
                'models': [],
                'recommendations': []
            }
            
            # Basic dataset summary
            report['summary'] = {
                'total_rows': len(df),
                'total_columns': len(df.columns),
                'missing_values': int(df.isnull().sum().sum()),
                'missing_percentage': float((df.isnull().sum().sum() / df.size) * 100),
                'memory_usage_mb': float(df.memory_usage(deep=True).sum() / 1024 / 1024),
                'data_types': df.dtypes.astype(str).to_dict(),
                'duplicate_rows': int(df.duplicated().sum()),
                'numeric_columns': len(df.select_dtypes(include=['number']).columns),
                'categorical_columns': len(df.select_dtypes(include=['object', 'category']).columns)
            }
            
            # EDA Results
            try:
                eda_results = self.eda_engine.generate_basic_statistics(df)
                report['eda_results'] = eda_results
            except Exception as e:
                logging.warning(f"EDA analysis failed: {str(e)}")
                report['eda_results'] = {'error': str(e)}
            
            # Statistical Tests
            try:
                stats_results = self.stats_engine.comprehensive_statistical_analysis(df)
                report['statistical_tests'] = stats_results
            except Exception as e:
                logging.warning(f"Statistical analysis failed: {str(e)}")
                report['statistical_tests'] = {'error': str(e)}
            
            # Generate key visualizations
            try:
                visualizations = self._generate_key_visualizations(df)
                report['visualizations'] = visualizations
            except Exception as e:
                logging.warning(f"Visualization generation failed: {str(e)}")
                report['visualizations'] = {'error': str(e)}
            
            # Get stored analyses
            analyses = Analysis.query.filter_by(dataset_id=dataset_id).all()
            report['stored_analyses'] = [analysis.to_dict() for analysis in analyses]
            
            # Get trained models
            models = ModelTraining.query.filter_by(dataset_id=dataset_id).all()
            for model in models:
                model_info = model.to_dict()
                model_info['performance_metrics'] = model.get_performance_metrics()
                report['models'].append(model_info)
            
            # Generate recommendations
            try:
                recommendations = self._generate_recommendations(df)
                report['recommendations'] = recommendations
            except Exception as e:
                logging.warning(f"Recommendations generation failed: {str(e)}")
                report['recommendations'] = {'error': str(e)}
            
            return report
            
        except Exception as e:
            logging.error(f"Error generating comprehensive report: {str(e)}")
            return {'error': str(e)}
    
    def _generate_key_visualizations(self, df):
        """Generate key visualizations for the report"""
        visualizations = {}
        
        # Correlation heatmap for numeric data
        numeric_cols = df.select_dtypes(include=['number']).columns
        if len(numeric_cols) >= 2:
            try:
                corr_viz = self.viz_engine.create_correlation_heatmap(df)
                if 'error' not in corr_viz:
                    visualizations['correlation_heatmap'] = corr_viz
            except Exception as e:
                logging.warning(f"Failed to create correlation heatmap: {str(e)}")
        
        # Distribution plots for key numeric columns
        for col in numeric_cols[:3]:  # Top 3 numeric columns
            try:
                dist_viz = self.viz_engine.create_distribution_plot(df, col)
                if 'error' not in dist_viz:
                    visualizations[f'distribution_{col}'] = dist_viz
            except Exception as e:
                logging.warning(f"Failed to create distribution plot for {col}: {str(e)}")
        
        # Bar charts for key categorical columns
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns
        for col in categorical_cols[:3]:  # Top 3 categorical columns
            try:
                bar_viz = self.viz_engine.create_bar_chart(df, col)
                if 'error' not in bar_viz:
                    visualizations[f'bar_chart_{col}'] = bar_viz
            except Exception as e:
                logging.warning(f"Failed to create bar chart for {col}: {str(e)}")
        
        return visualizations
    
    def _generate_recommendations(self, df):
        """Generate actionable recommendations based on data analysis"""
        recommendations = []
        
        # Data quality recommendations
        missing_percentage = (df.isnull().sum().sum() / df.size) * 100
        if missing_percentage > 20:
            recommendations.append({
                'category': 'data_quality',
                'priority': 'high',
                'title': 'Address Missing Data',
                'description': f'{missing_percentage:.1f}% of data is missing. Consider imputation or data collection review.',
                'action_items': [
                    'Analyze missing data patterns',
                    'Implement appropriate imputation strategies',
                    'Consider data collection process review'
                ]
            })
        
        # Duplicate data recommendations
        duplicate_count = df.duplicated().sum()
        if duplicate_count > 0:
            recommendations.append({
                'category': 'data_quality',
                'priority': 'medium',
                'title': 'Remove Duplicate Records',
                'description': f'Found {duplicate_count} duplicate rows ({(duplicate_count/len(df)*100):.1f}%).',
                'action_items': [
                    'Review duplicate records',
                    'Determine deduplication strategy',
                    'Clean dataset before analysis'
                ]
            })
        
        # Feature engineering recommendations
        numeric_cols = df.select_dtypes(include=['number']).columns
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns
        
        if len(numeric_cols) >= 2:
            recommendations.append({
                'category': 'feature_engineering',
                'priority': 'medium',
                'title': 'Consider Feature Interactions',
                'description': 'Multiple numeric features available for creating interaction terms.',
                'action_items': [
                    'Create polynomial features',
                    'Generate interaction terms',
                    'Apply dimensionality reduction if needed'
                ]
            })
        
        # High cardinality categorical features
        high_cardinality_cols = []
        for col in categorical_cols:
            if df[col].nunique() > 50:
                high_cardinality_cols.append(col)
        
        if high_cardinality_cols:
            recommendations.append({
                'category': 'preprocessing',
                'priority': 'high',
                'title': 'Handle High Cardinality Features',
                'description': f'Features {high_cardinality_cols} have high cardinality.',
                'action_items': [
                    'Consider target encoding',
                    'Group rare categories',
                    'Use frequency encoding'
                ]
            })
        
        # Scaling recommendations
        if len(numeric_cols) > 1:
            ranges = [df[col].max() - df[col].min() for col in numeric_cols if df[col].notna().any()]
            if ranges and max(ranges) / min(ranges) > 100:
                recommendations.append({
                    'category': 'preprocessing',
                    'priority': 'high',
                    'title': 'Scale Numeric Features',
                    'description': 'Numeric features have very different scales.',
                    'action_items': [
                        'Apply StandardScaler or RobustScaler',
                        'Consider log transformation for skewed data',
                        'Normalize features for distance-based algorithms'
                    ]
                })
        
        return recommendations
    
    def generate_pdf_report(self, dataset_id):
        """Generate PDF report - enhanced implementation"""
        try:
            # Get comprehensive report data
            report_data = self.generate_comprehensive_report(dataset_id)
            
            if 'error' in report_data:
                raise Exception(report_data['error'])
            
            # Create temporary directory for PDF generation
            temp_dir = tempfile.mkdtemp()
            
            # For now, save as enhanced JSON with formatting
            # In production, you would use libraries like reportlab, weasyprint, etc.
            pdf_path = os.path.join(temp_dir, f'report_{dataset_id}.json')
            
            # Format the report for better readability
            formatted_report = self._format_report_for_export(report_data)
            
            with open(pdf_path, 'w') as f:
                json.dump(formatted_report, f, indent=2, default=str)
            
            return pdf_path
            
        except Exception as e:
            logging.error(f"Error generating PDF report: {str(e)}")
            raise e
    
    def _format_report_for_export(self, report_data):
        """Format report data for export with better structure"""
        formatted = {
            'DATASET_ANALYSIS_REPORT': {
                'dataset_information': report_data.get('dataset_info', {}),
                'generation_timestamp': report_data.get('generated_at'),
                'executive_summary': {
                    'total_records': report_data.get('summary', {}).get('total_rows', 0),
                    'total_features': report_data.get('summary', {}).get('total_columns', 0),
                    'data_quality_score': self._calculate_data_quality_score(report_data.get('summary', {})),
                    'key_findings': self._extract_key_findings(report_data)
                },
                'detailed_analysis': {
                    'data_overview': report_data.get('summary', {}),
                    'exploratory_analysis': report_data.get('eda_results', {}),
                    'statistical_tests': report_data.get('statistical_tests', {}),
                    'visualizations_summary': self._summarize_visualizations(report_data.get('visualizations', {}))
                },
                'machine_learning_models': report_data.get('models', []),
                'recommendations': report_data.get('recommendations', []),
                'stored_analyses': report_data.get('stored_analyses', [])
            }
        }
        
        return formatted
    
    def _calculate_data_quality_score(self, summary):
        """Calculate a data quality score from 0-100"""
        try:
            score = 100
            
            # Deduct for missing values
            missing_pct = summary.get('missing_percentage', 0)
            score -= min(missing_pct, 50)  # Max 50 point deduction
            
            # Deduct for duplicates
            total_rows = summary.get('total_rows', 1)
            duplicate_rows = summary.get('duplicate_rows', 0)
            duplicate_pct = (duplicate_rows / total_rows) * 100
            score -= min(duplicate_pct, 30)  # Max 30 point deduction
            
            return max(score, 0)
        except:
            return 50  # Default score if calculation fails
    
    def _extract_key_findings(self, report_data):
        """Extract key findings from the analysis"""
        findings = []
        
        summary = report_data.get('summary', {})
        
        # Data size finding
        total_rows = summary.get('total_rows', 0)
        if total_rows > 100000:
            findings.append(f"Large dataset with {total_rows:,} records - suitable for robust analysis")
        elif total_rows < 1000:
            findings.append(f"Small dataset with {total_rows:,} records - limited statistical power")
        
        # Missing data finding
        missing_pct = summary.get('missing_percentage', 0)
        if missing_pct > 20:
            findings.append(f"High missing data rate ({missing_pct:.1f}%) requires attention")
        elif missing_pct < 5:
            findings.append("Good data completeness with minimal missing values")
        
        # Data types finding
        numeric_cols = summary.get('numeric_columns', 0)
        categorical_cols = summary.get('categorical_columns', 0)
        
        if numeric_cols > categorical_cols:
            findings.append("Predominantly numeric dataset - suitable for regression analysis")
        elif categorical_cols > numeric_cols:
            findings.append("Predominantly categorical dataset - classification focus recommended")
        else:
            findings.append("Balanced mix of numeric and categorical features")
        
        return findings
    
    def _summarize_visualizations(self, visualizations):
        """Summarize the visualizations generated"""
        summary = {
            'total_visualizations': len(visualizations),
            'types_generated': [],
            'available_plots': list(visualizations.keys())
        }
        
        # Categorize visualization types
        if any('correlation' in key for key in visualizations.keys()):
            summary['types_generated'].append('correlation_analysis')
        
        if any('distribution' in key for key in visualizations.keys()):
            summary['types_generated'].append('distribution_analysis')
        
        if any('bar_chart' in key for key in visualizations.keys()):
            summary['types_generated'].append('categorical_analysis')
        
        return summary
    
    def generate_summary_report(self, dataset_id):
        """Generate a shorter summary report"""
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            
            # Load dataset
            df, _ = self.data_processor.load_file(dataset.file_path)
            if df is None:
                return {'error': 'Could not load dataset'}
            
            # Generate basic summary
            numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
            categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
            
            summary = {
                'dataset_info': dataset.to_dict(),
                'generated_at': datetime.now().isoformat(),
                'basic_stats': {
                    'total_rows': len(df),
                    'total_columns': len(df.columns),
                    'numeric_columns': len(numeric_cols),
                    'categorical_columns': len(categorical_cols),
                    'missing_values': int(df.isnull().sum().sum()),
                    'missing_percentage': float((df.isnull().sum().sum() / df.size) * 100),
                    'duplicated_rows': int(df.duplicated().sum()),
                    'memory_usage_mb': float(df.memory_usage(deep=True).sum() / 1024 / 1024)
                },
                'column_info': []
            }
            
            # Add column information
            for col in df.columns:
                col_info = {
                    'name': col,
                    'type': str(df[col].dtype),
                    'missing_count': int(df[col].isnull().sum()),
                    'missing_percentage': float((df[col].isnull().sum() / len(df)) * 100),
                    'unique_count': int(df[col].nunique()),
                    'unique_percentage': float((df[col].nunique() / len(df)) * 100)
                }
                
                if col in numeric_cols and df[col].notna().any():
                    col_info.update({
                        'mean': float(df[col].mean()) if pd.notna(df[col].mean()) else None,
                        'std': float(df[col].std()) if pd.notna(df[col].std()) else None,
                        'min': float(df[col].min()) if pd.notna(df[col].min()) else None,
                        'max': float(df[col].max()) if pd.notna(df[col].max()) else None,
                        'median': float(df[col].median()) if pd.notna(df[col].median()) else None
                    })
                elif col in categorical_cols:
                    value_counts = df[col].value_counts()
                    if len(value_counts) > 0:
                        col_info.update({
                            'most_frequent_value': str(value_counts.index[0]),
                            'most_frequent_count': int(value_counts.iloc[0]),
                            'least_frequent_value': str(value_counts.index[-1]),
                            'least_frequent_count': int(value_counts.iloc[-1])
                        })
                
                summary['column_info'].append(col_info)
            
            return summary
            
        except Exception as e:
            logging.error(f"Error generating summary report: {str(e)}")
            return {'error': str(e)}
    
    def export_report(self, dataset_id, format_type='json'):
        """Export report in different formats"""
        try:
            if format_type.lower() == 'json':
                return self.generate_comprehensive_report(dataset_id)
            elif format_type.lower() == 'summary':
                return self.generate_summary_report(dataset_id)
            elif format_type.lower() == 'pdf':
                return self.generate_pdf_report(dataset_id)
            else:
                return {'error': f'Unsupported format: {format_type}'}
                
        except Exception as e:
            logging.error(f"Error exporting report: {str(e)}")
            return {'error': str(e)}