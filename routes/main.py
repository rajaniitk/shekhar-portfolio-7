from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from models import Dataset, Analysis, ModelTraining
from app import db
from flask import jsonify
import tempfile
import os

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Main dashboard showing recent datasets and analyses"""
    try:
        recent_datasets = Dataset.query.order_by(Dataset.upload_date.desc()).limit(5).all()
        recent_analyses = Analysis.query.order_by(Analysis.created_date.desc()).limit(10).all()
        
        # Get statistics for dashboard
        total_datasets = Dataset.query.count()
        total_analyses = Analysis.query.count()
        total_models = ModelTraining.query.count()
        
        stats = {
            'total_datasets': total_datasets,
            'total_analyses': total_analyses,
            'total_models': total_models
        }
        
        # Convert datasets to dictionaries for JSON serialization
        datasets_data = [dataset.to_dict() for dataset in recent_datasets]
        
        # Convert analyses to dictionaries for JSON serialization
        analyses_data = [analysis.to_dict() for analysis in recent_analyses]
        
        return render_template('index.html', 
                             recent_datasets=datasets_data,
                             recent_analyses=analyses_data,
                             stats=stats)
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return render_template('index.html', 
                             recent_datasets=[],
                             recent_analyses=[],
                             stats={'total_datasets': 0, 'total_analyses': 0, 'total_models': 0})

@main_bp.route('/dashboard')
def dashboard():
    """Main analysis dashboard"""
    try:
        datasets = Dataset.query.order_by(Dataset.upload_date.desc()).all()
        datasets_data = [dataset.to_dict() for dataset in datasets]
        return render_template('analysis_dashboard.html', datasets=datasets_data)
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return render_template('analysis_dashboard.html', datasets=[])

@main_bp.route('/reports')
def reports():
    """Reports and export page"""
    try:
        datasets = Dataset.query.order_by(Dataset.upload_date.desc()).all()
        datasets_data = [dataset.to_dict() for dataset in datasets]
        return render_template('reports.html', datasets=datasets_data)
    except Exception as e:
        flash(f'Error loading reports page: {str(e)}', 'error')
        return render_template('reports.html', datasets=[])

@main_bp.route('/api/reports/generate/<int:dataset_id>')
def generate_report(dataset_id):
    """Generate a comprehensive report for a dataset"""
    from services.report_generator import ReportGenerator
    
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        report_generator = ReportGenerator()
        report_data = report_generator.generate_comprehensive_report(dataset_id)

        if 'error' in report_data:
            return jsonify(report_data), 500
        
        return jsonify(report_data)
        
    except Exception as e:
        flash(f"Error generating report: {str(e)}", 'error')
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/reports/summary/<int:dataset_id>')
def generate_summary_report(dataset_id):
    """Generate a summary report for a dataset"""
    from services.report_generator import ReportGenerator
    
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        report_generator = ReportGenerator()
        report_data = report_generator.generate_summary_report(dataset_id)

        if 'error' in report_data:
            return jsonify(report_data), 500
        
        return jsonify(report_data)
        
    except Exception as e:
        flash(f"Error generating summary report: {str(e)}", 'error')
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/reports/download/<int:dataset_id>')
def download_report(dataset_id):
    """Download the report in different formats"""
    from services.report_generator import ReportGenerator
    
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        report_format = request.args.get('format', 'json').lower()
        
        report_generator = ReportGenerator()

        if report_format == 'json':
            report_data = report_generator.generate_comprehensive_report(dataset_id)
            if 'error' in report_data:
                return jsonify(report_data), 500
            return jsonify(report_data)
        
        elif report_format == 'summary':
            report_data = report_generator.generate_summary_report(dataset_id)
            if 'error' in report_data:
                return jsonify(report_data), 500
            return jsonify(report_data)
        
        elif report_format == 'pdf':
            # Generate the report and save it to a temporary file
            try:
                pdf_path = report_generator.generate_pdf_report(dataset_id)
                
                # Check if file exists
                if not os.path.exists(pdf_path):
                    return jsonify({'error': 'Report file not found'}), 500
                
                return send_file(
                    pdf_path, 
                    as_attachment=True, 
                    download_name=f'report_{dataset.filename}_{dataset_id}.json',
                    mimetype='application/json'
                )
            except Exception as pdf_error:
                return jsonify({'error': f'PDF generation failed: {str(pdf_error)}'}), 500
        
        else:
            return jsonify({'error': f'Unsupported format: {report_format}'}), 400
        
    except Exception as e:
        flash(f"Error downloading report: {str(e)}", 'error')
        return jsonify({'error': str(e)}), 500

@main_bp.route('/delete_dataset/<int:dataset_id>')
def delete_dataset(dataset_id):
    """Delete a dataset and all associated analyses"""
    try:
        dataset = Dataset.query.get_or_404(dataset_id)
        
        # Delete associated analyses and models
        Analysis.query.filter_by(dataset_id=dataset_id).delete()
        
        # Delete model files and records
        models = ModelTraining.query.filter_by(dataset_id=dataset_id).all()
        for model in models:
            # Try to delete model file
            try:
                if model.model_path and os.path.exists(model.model_path):
                    os.remove(model.model_path)
            except Exception as file_error:
                # Log but don't fail the deletion
                flash(f'Warning: Could not delete model file: {str(file_error)}', 'warning')
        
        ModelTraining.query.filter_by(dataset_id=dataset_id).delete()
        
        # Try to delete dataset file
        try:
            if dataset.file_path and os.path.exists(dataset.file_path):
                os.remove(dataset.file_path)
        except Exception as file_error:
            # Log but don't fail the deletion
            flash(f'Warning: Could not delete dataset file: {str(file_error)}', 'warning')
        
        # Delete the dataset record
        db.session.delete(dataset)
        db.session.commit()
        
        flash('Dataset and all associated analyses have been deleted successfully.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting dataset: {str(e)}', 'error')
    
    return redirect(url_for('main.index'))

@main_bp.route('/debug_test')
def debug_test():
    """Debug route to test data serialization"""
    from datetime import datetime
    
    # Test with actual database data if available
    try:
        dataset = Dataset.query.first()
        if dataset:
            dataset_dict = dataset.to_dict()
            print("Dataset to_dict() result:")
            print(f"  upload_date type: {type(dataset_dict['upload_date'])}")
            print(f"  upload_date value: {dataset_dict['upload_date']}")
            
            # Test the template expression that's causing the error
            if dataset_dict['upload_date']:
                formatted_date = dataset_dict['upload_date'][:16].replace('T', ' ')
                print(f"  formatted date: {formatted_date}")
            
            return f"<h1>Debug Test Results</h1><p>Dataset ID: {dataset_dict['id']}</p><p>Filename: {dataset_dict['filename']}</p><p>Upload Date: {dataset_dict['upload_date']}</p><p>Date Type: {type(dataset_dict['upload_date'])}</p>"
        else:
            return "<h1>Debug Test</h1><p>No datasets found in database</p>"
            
    except Exception as e:
        return f"<h1>Debug Test Error</h1><p>Error: {str(e)}</p><p>Error Type: {type(e).__name__}</p>"
 