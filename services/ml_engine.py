import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV, RandomizedSearchCV
from sklearn.preprocessing import StandardScaler, LabelEncoder, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, roc_auc_score,
    mean_squared_error, mean_absolute_error, r2_score, classification_report,
    confusion_matrix, roc_curve, precision_recall_curve
)

# Classification algorithms
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.tree import DecisionTreeClassifier
try:
    from xgboost import XGBClassifier
    HAS_XGB = True
except ImportError:
    HAS_XGB = False
# try:
#     from lightgbm import LGBMClassifier
#     HAS_LGBM = True
# except ImportError:
HAS_LGBM = False

# Regression algorithms
from sklearn.linear_model import LinearRegression, Ridge, Lasso, ElasticNet
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.svm import SVR
from sklearn.neighbors import KNeighborsRegressor
from sklearn.tree import DecisionTreeRegressor
try:
    from xgboost import XGBRegressor
except ImportError:
    pass
# try:
#     from lightgbm import LGBMRegressor
# except ImportError:
#     pass

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import logging
import json

class MLEngine:
    """Comprehensive Machine Learning Engine with 10+ algorithms"""
    
    def __init__(self):
        self.plotly_template = "plotly_dark"
        
        # Classification models
        self.classification_models = {
            'logistic_regression': LogisticRegression(random_state=42),
            'random_forest': RandomForestClassifier(random_state=42),
            'gradient_boosting': GradientBoostingClassifier(random_state=42),
            'svm': SVC(random_state=42, probability=True),
            'knn': KNeighborsClassifier(),
            'naive_bayes': GaussianNB(),
            'decision_tree': DecisionTreeClassifier(random_state=42),
        }
        
        if HAS_XGB:
            self.classification_models['xgboost'] = XGBClassifier(random_state=42, eval_metric='logloss')
        # if HAS_LGBM:
        #     self.classification_models['lightgbm'] = LGBMClassifier(random_state=42)
        
        # Regression models
        self.regression_models = {
            'linear_regression': LinearRegression(),
            'ridge': Ridge(random_state=42),
            'lasso': Lasso(random_state=42),
            'elastic_net': ElasticNet(random_state=42),
            'random_forest': RandomForestRegressor(random_state=42),
            'gradient_boosting': GradientBoostingRegressor(random_state=42),
            'svr': SVR(),
            'knn': KNeighborsRegressor(),
            'decision_tree': DecisionTreeRegressor(random_state=42),
        }
        
        if HAS_XGB:
            self.regression_models['xgboost'] = XGBRegressor(random_state=42)
        # if HAS_LGBM:
        #     self.regression_models['lightgbm'] = LGBMRegressor(random_state=42)
    
    def _make_json_serializable(self, obj):
        """Convert numpy/pandas objects to JSON serializable formats"""
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, pd.Series):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {k: self._make_json_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_json_serializable(item) for item in obj]
        else:
            return obj
    
    def preprocess_data(self, df, target_column, feature_columns):
        """Preprocess data for machine learning"""
        try:
            # Prepare features and target
            X = df[feature_columns].copy()
            y = df[target_column].copy()
            
            # Remove rows with missing target values
            mask = ~y.isnull()
            X = X[mask]
            y = y[mask]
            
            if len(X) == 0:
                return None, None, None, {'error': 'No valid data after removing missing target values'}
            
            # Identify column types
            numeric_features = X.select_dtypes(include=[np.number]).columns.tolist()
            categorical_features = X.select_dtypes(include=['object', 'category']).columns.tolist()
            
            # Create preprocessor
            preprocessor = ColumnTransformer(
                transformers=[
                    ('num', Pipeline([
                        ('imputer', SimpleImputer(strategy='median')),
                        ('scaler', StandardScaler())
                    ]), numeric_features),
                    ('cat', Pipeline([
                        ('imputer', SimpleImputer(strategy='constant', fill_value='missing')),
                        ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
                    ]), categorical_features)
                ],
                remainder='drop'
            )
            
            # Determine problem type and encode target
            if y.dtype in ['object', 'category'] or y.nunique() <= 20:
                problem_type = 'classification'
                # Encode target for classification
                if y.dtype in ['object', 'category']:
                    label_encoder = LabelEncoder()
                    y_encoded = label_encoder.fit_transform(y.astype(str))
                    target_encoder_classes = label_encoder.classes_.tolist()
                else:
                    y_encoded = y
                    target_encoder_classes = None
            else:
                problem_type = 'regression'
                y_encoded = y
                target_encoder_classes = None
            
            return X, y_encoded, preprocessor, {
                'problem_type': problem_type, 
                'target_encoder_classes': target_encoder_classes
            }
            
        except Exception as e:
            logging.error(f"Error preprocessing data: {str(e)}")
            return None, None, None, {'error': str(e)}
    
    def train_model(self, df, target_column, feature_columns, model_type, problem_type='auto', hyperparameters=None):
        """Train a machine learning model"""
        try:
            # Preprocess data
            X, y, preprocessor, prep_info = self.preprocess_data(df, target_column, feature_columns)
            
            if X is None:
                return {'success': False, 'error': prep_info.get('error', 'Unknown preprocessing error')}
            
            # Determine problem type if auto
            if problem_type == 'auto':
                problem_type = prep_info['problem_type']
            
            # Select model
            if problem_type == 'classification':
                if model_type not in self.classification_models:
                    return {'success': False, 'error': f'Unknown classification model: {model_type}'}
                model = self.classification_models[model_type]
            else:
                if model_type not in self.regression_models:
                    return {'success': False, 'error': f'Unknown regression model: {model_type}'}
                model = self.regression_models[model_type]
            
            # Apply hyperparameters
            if hyperparameters:
                model.set_params(**hyperparameters)
            
            # Create pipeline
            pipeline = Pipeline([
                ('preprocessor', preprocessor),
                ('classifier' if problem_type == 'classification' else 'regressor', model)
            ])
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Train model
            pipeline.fit(X_train, y_train)
            
            # Make predictions
            y_pred = pipeline.predict(X_test)
            
            # Calculate metrics
            if problem_type == 'classification':
                metrics = self._calculate_classification_metrics(y_test, y_pred, pipeline, X_test)
            else:
                metrics = self._calculate_regression_metrics(y_test, y_pred)
            
            # Cross-validation score
            cv_scores = cross_val_score(pipeline, X, y, cv=5)
            metrics['cv_mean'] = float(cv_scores.mean())
            metrics['cv_std'] = float(cv_scores.std())
            
            # Make all metrics JSON serializable
            metrics = self._make_json_serializable(metrics)
            
            return {
                'success': True,
                'model': pipeline,
                'metrics': metrics,
                'problem_type': problem_type,
                'feature_columns': feature_columns,
                'target_column': target_column,
                'target_encoder_classes': prep_info.get('target_encoder_classes')
            }
            
        except Exception as e:
            logging.error(f"Error training model: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _calculate_classification_metrics(self, y_true, y_pred, pipeline, X_test):
        """Calculate classification metrics"""
        metrics = {
            'accuracy': float(accuracy_score(y_true, y_pred)),
            'precision': float(precision_score(y_true, y_pred, average='weighted', zero_division=0)),
            'recall': float(recall_score(y_true, y_pred, average='weighted', zero_division=0)),
            'f1_score': float(f1_score(y_true, y_pred, average='weighted', zero_division=0))
        }
        
        # ROC AUC for binary classification
        if len(np.unique(y_true)) == 2:
            try:
                y_proba = pipeline.predict_proba(X_test)[:, 1]
                metrics['roc_auc'] = float(roc_auc_score(y_true, y_proba))
            except:
                pass
        
        # Confusion matrix
        cm = confusion_matrix(y_true, y_pred)
        metrics['confusion_matrix'] = cm.tolist()
        
        # Classification report
        try:
            report = classification_report(y_true, y_pred, output_dict=True, zero_division=0)
            metrics['classification_report'] = self._make_json_serializable(report)
        except:
            metrics['classification_report'] = {}
        
        return metrics
    
    def _calculate_regression_metrics(self, y_true, y_pred):
        """Calculate regression metrics"""
        # Ensure arrays are numeric and handle any remaining issues
        y_true = pd.to_numeric(y_true, errors='coerce')
        y_pred = pd.to_numeric(y_pred, errors='coerce')
        
        # Remove NaN values
        mask = ~(np.isnan(y_true) | np.isnan(y_pred))
        y_true = y_true[mask]
        y_pred = y_pred[mask]
        
        if len(y_true) == 0:
            return {'error': 'No valid predictions for metric calculation'}
        
        metrics = {
            'mse': float(mean_squared_error(y_true, y_pred)),
            'rmse': float(np.sqrt(mean_squared_error(y_true, y_pred))),
            'mae': float(mean_absolute_error(y_true, y_pred)),
            'r2': float(r2_score(y_true, y_pred))
        }
        
        # Additional metrics
        if np.all(y_true != 0):
            mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100
            metrics['mape'] = float(mape)
        else:
            metrics['mape'] = None
        
        return metrics
    
    def evaluate_model(self, model, df, target_column, feature_columns):
        """Evaluate a trained model"""
        try:
            # Prepare data
            X = df[feature_columns]
            y = df[target_column]
            
            # Remove missing values
            mask = ~(X.isnull().any(axis=1) | y.isnull())
            X = X[mask]
            y = y[mask]
            
            if len(X) == 0:
                return {'error': 'No valid data for evaluation'}
            
            # Make predictions
            y_pred = model.predict(X)
            
            # Determine problem type
            if hasattr(model, 'predict_proba'):
                problem_type = 'classification'
                
                # Handle target encoding consistency
                if hasattr(model, 'classes_'):
                    try:
                        # Try to use model classes if available
                        if y.dtype in ['object', 'category']:
                            label_encoder = LabelEncoder()
                            y_encoded = label_encoder.fit_transform(y.astype(str))
                        else:
                            y_encoded = y
                        
                        metrics = self._calculate_classification_metrics(y_encoded, y_pred, model, X)
                    except Exception as e:
                        logging.error(f"Classification evaluation error: {str(e)}")
                        return {'error': f'Classification evaluation failed: {str(e)}'}
                else:
                    # Fallback to categorical codes
                    if y.dtype in ['object', 'category']:
                        y_codes = pd.Categorical(y).codes
                    else:
                        y_codes = y
                    
                    metrics = self._calculate_classification_metrics(y_codes, y_pred, model, X)
                
                # Generate visualization data
                viz_data = self._create_classification_visualizations(y_encoded if 'y_encoded' in locals() else y_codes, y_pred, model, X)
                
            else:
                problem_type = 'regression'
                
                # For regression ensure y and y_pred are numeric
                y_numeric = pd.to_numeric(y, errors='coerce')
                y_pred_numeric = pd.to_numeric(y_pred, errors='coerce')
                
                # Remove any NaN values after conversion
                valid_mask = ~(pd.isna(y_numeric) | pd.isna(y_pred_numeric))
                y_numeric = y_numeric[valid_mask]
                y_pred_numeric = y_pred_numeric[valid_mask]
                
                if len(y_numeric) == 0:
                    return {'error': 'No valid data for regression evaluation'}
                
                metrics = self._calculate_regression_metrics(y_numeric, y_pred_numeric)
                
                # Generate visualization data
                viz_data = self._create_regression_visualizations(y_numeric, y_pred_numeric)
            
            # Make results JSON serializable
            metrics = self._make_json_serializable(metrics)
            viz_data = self._make_json_serializable(viz_data)
            
            return {
                'metrics': metrics,
                'visualizations': viz_data,
                'problem_type': problem_type
            }
            
        except Exception as e:
            logging.error(f"Error evaluating model: {str(e)}")
            return {'error': str(e)}
    
    def _create_classification_visualizations(self, y_true, y_pred, model, X_test):
        """Create visualizations for classification results"""
        visualizations = {}
        
        try:
            # Confusion Matrix
            cm = confusion_matrix(y_true, y_pred)
            
            fig_cm = go.Figure(data=go.Heatmap(
                z=cm,
                x=[f'Predicted {i}' for i in range(len(cm))],
                y=[f'Actual {i}' for i in range(len(cm))],
                colorscale='Blues',
                text=cm,
                texttemplate="%{text}",
                textfont={"size": 12}
            ))
            
            fig_cm.update_layout(
                title='Confusion Matrix',
                template=self.plotly_template
            )
            
            visualizations['confusion_matrix'] = fig_cm.to_json()
            
            # ROC Curve (for binary classification)
            if len(np.unique(y_true)) == 2 and hasattr(model, 'predict_proba'):
                try:
                    y_proba = model.predict_proba(X_test)[:, 1]
                    fpr, tpr, _ = roc_curve(y_true, y_proba)
                    auc = roc_auc_score(y_true, y_proba)
                    
                    fig_roc = go.Figure()
                    fig_roc.add_trace(go.Scatter(
                        x=fpr, y=tpr,
                        mode='lines',
                        name=f'ROC Curve (AUC = {auc:.3f})'
                    ))
                    fig_roc.add_trace(go.Scatter(
                        x=[0, 1], y=[0, 1],
                        mode='lines',
                        line=dict(dash='dash'),
                        name='Random Classifier'
                    ))
                    
                    fig_roc.update_layout(
                        title='ROC Curve',
                        xaxis_title='False Positive Rate',
                        yaxis_title='True Positive Rate',
                        template=self.plotly_template
                    )
                    
                    visualizations['roc_curve'] = fig_roc.to_json()
                    
                    # Precision-Recall Curve
                    precision, recall, _ = precision_recall_curve(y_true, y_proba)
                    
                    fig_pr = go.Figure()
                    fig_pr.add_trace(go.Scatter(
                        x=recall, y=precision,
                        mode='lines',
                        name='Precision-Recall Curve'
                    ))
                    
                    fig_pr.update_layout(
                        title='Precision-Recall Curve',
                        xaxis_title='Recall',
                        yaxis_title='Precision',
                        template=self.plotly_template
                    )
                    
                    visualizations['precision_recall'] = fig_pr.to_json()
                except Exception as e:
                    logging.warning(f"Could not create ROC/PR curves: {str(e)}")
            
        except Exception as e:
            logging.error(f"Error creating classification visualizations: {str(e)}")
        
        return visualizations
    
    def _create_regression_visualizations(self, y_true, y_pred):
        """Create visualizations for regression results"""
        visualizations = {}
        
        try:
            # Actual vs Predicted
            fig_scatter = go.Figure()
            fig_scatter.add_trace(go.Scatter(
                x=y_true, y=y_pred,
                mode='markers',
                name='Predictions',
                marker=dict(size=6, opacity=0.6)
            ))
            
            # Perfect prediction line
            min_val = min(min(y_true), min(y_pred))
            max_val = max(max(y_true), max(y_pred))
            fig_scatter.add_trace(go.Scatter(
                x=[min_val, max_val], y=[min_val, max_val],
                mode='lines',
                name='Perfect Prediction',
                line=dict(color='red', dash='dash')
            ))
            
            fig_scatter.update_layout(
                title='Actual vs Predicted Values',
                xaxis_title='Actual Values',
                yaxis_title='Predicted Values',
                template=self.plotly_template
            )
            
            visualizations['actual_vs_predicted'] = fig_scatter.to_json()
            
            # Residuals plot
            residuals = y_true - y_pred
            
            fig_residuals = go.Figure()
            fig_residuals.add_trace(go.Scatter(
                x=y_pred, y=residuals,
                mode='markers',
                name='Residuals',
                marker=dict(size=6, opacity=0.6)
            ))
            
            fig_residuals.add_hline(y=0, line_dash="dash", line_color="red")
            
            fig_residuals.update_layout(
                title='Residuals Plot',
                xaxis_title='Predicted Values',
                yaxis_title='Residuals',
                template=self.plotly_template
            )
            
            visualizations['residuals'] = fig_residuals.to_json()
            
            # Residuals histogram
            fig_hist = go.Figure()
            fig_hist.add_trace(go.Histogram(
                x=residuals,
                nbinsx=30,
                name='Residuals Distribution'
            ))
            
            fig_hist.update_layout(
                title='Distribution of Residuals',
                xaxis_title='Residuals',
                yaxis_title='Frequency',
                template=self.plotly_template
            )
            
            visualizations['residuals_histogram'] = fig_hist.to_json()
            
        except Exception as e:
            logging.error(f"Error creating regression visualizations: {str(e)}")
        
        return visualizations
    
    def make_predictions(self, model, input_data, feature_columns):
        """Make predictions with a trained model"""
        try:
            # Prepare input data
            input_df = pd.DataFrame([input_data])
            
            # Ensure all feature columns are present
            for col in feature_columns:
                if col not in input_df.columns:
                    input_df[col] = None
            
            # Select only feature columns in correct order
            input_df = input_df[feature_columns]
            
            # Make prediction
            prediction = model.predict(input_df)
            
            result = {
                'prediction': float(prediction[0]) if len(prediction) == 1 else [float(p) for p in prediction]
            }
            
            # Add probability for classification
            if hasattr(model, 'predict_proba'):
                proba = model.predict_proba(input_df)
                result['probability'] = [float(p) for p in proba[0]]
                if hasattr(model, 'classes_'):
                    result['classes'] = [str(c) for c in model.classes_]
            
            return result
            
        except Exception as e:
            logging.error(f"Error making predictions: {str(e)}")
            return {'error': str(e)}
    
    def get_feature_importance(self, model, feature_columns):
        """Get feature importance for a trained model"""
        try:
            # Get the actual model from pipeline
            if hasattr(model, 'named_steps'):
                actual_model = model.named_steps.get('classifier') or model.named_steps.get('regressor')
            else:
                actual_model = model
            
            importance_data = {}
            
            # Different methods to get feature importance
            if hasattr(actual_model, 'feature_importances_'):
                # Tree-based models
                feature_names = self._get_feature_names_from_pipeline(model, feature_columns)
                importances = actual_model.feature_importances_
                
                importance_data['feature_importance'] = dict(zip(feature_names, [float(imp) for imp in importances]))
                importance_data['method'] = 'built_in_importance'
                
            elif hasattr(actual_model, 'coef_'):
                # Linear models
                feature_names = self._get_feature_names_from_pipeline(model, feature_columns)
                
                if len(actual_model.coef_.shape) == 1:
                    # Binary classification or regression
                    coefficients = actual_model.coef_
                else:
                    # Multi-class classification - use mean absolute coefficients
                    coefficients = np.mean(np.abs(actual_model.coef_), axis=0)
                
                importance_data['feature_importance'] = dict(zip(feature_names, [float(coef) for coef in coefficients]))
                importance_data['method'] = 'coefficients'
                
            else:
                # Permutation importance as fallback
                importance_data['feature_importance'] = dict(zip(feature_columns, [0.0] * len(feature_columns)))
                importance_data['method'] = 'not_available'
                importance_data['message'] = 'Feature importance not available for this model type'
            
            # Create visualization
            if importance_data['feature_importance']:
                sorted_features = sorted(importance_data['feature_importance'].items(), 
                                       key=lambda x: abs(x[1]), reverse=True)[:20]
                
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=[item[1] for item in sorted_features],
                    y=[item[0] for item in sorted_features],
                    orientation='h',
                    name='Feature Importance'
                ))
                
                fig.update_layout(
                    title='Feature Importance',
                    xaxis_title='Importance Score',
                    yaxis_title='Features',
                    template=self.plotly_template,
                    height=max(400, len(sorted_features) * 25)
                )
                
                importance_data['visualization'] = fig.to_json()
            
            return importance_data
            
        except Exception as e:
            logging.error(f"Error getting feature importance: {str(e)}")
            return {'error': str(e)}
    
    def _get_feature_names_from_pipeline(self, pipeline, original_features):
        """Extract feature names from preprocessing pipeline"""
        try:
            if hasattr(pipeline, 'named_steps') and 'preprocessor' in pipeline.named_steps:
                preprocessor = pipeline.named_steps['preprocessor']
                
                # Get feature names from ColumnTransformer
                if hasattr(preprocessor, 'get_feature_names_out'):
                    feature_names = preprocessor.get_feature_names_out().tolist()
                else:
                    # Fallback - construct names manually
                    feature_names = []
                    for name, transformer, columns in preprocessor.transformers_:
                        if name == 'num':
                            feature_names.extend(columns)
                        elif name == 'cat':
                            # OneHot encoder creates multiple features per categorical column
                            for col in columns:
                                # Approximate number of categories (this is a simplification)
                                feature_names.extend([f"{col}_{i}" for i in range(10)])
                
                return feature_names[:len(preprocessor.fit_transform(pd.DataFrame(columns=original_features, data=[range(len(original_features))]).iloc[:1])[0])]
            else:
                return original_features
                
        except Exception as e:
            logging.warning(f"Could not extract feature names: {str(e)}")
            return original_features
    
    def hyperparameter_tuning(self, df, target_column, feature_columns, model_type, problem_type='auto', param_grid=None):
        """Perform hyperparameter tuning"""
        try:
            # Preprocess data
            X, y, preprocessor, prep_info = self.preprocess_data(df, target_column, feature_columns)
            
            if X is None:
                return {'success': False, 'error': prep_info.get('error', 'Unknown preprocessing error')}
            
            # Determine problem type if auto
            if problem_type == 'auto':
                problem_type = prep_info['problem_type']
            
            # Select model
            if problem_type == 'classification':
                if model_type not in self.classification_models:
                    return {'success': False, 'error': f'Unknown classification model: {model_type}'}
                model = self.classification_models[model_type]
            else:
                if model_type not in self.regression_models:
                    return {'success': False, 'error': f'Unknown regression model: {model_type}'}
                model = self.regression_models[model_type]
            
            # Default parameter grids
            if param_grid is None:
                param_grid = self._get_default_param_grid(model_type, problem_type)
            
            # Create pipeline
            pipeline = Pipeline([
                ('preprocessor', preprocessor),
                ('classifier' if problem_type == 'classification' else 'regressor', model)
            ])
            
            # Adjust parameter keys for pipeline
            if param_grid:
                pipeline_param_grid = {}
                prefix = 'classifier__' if problem_type == 'classification' else 'regressor__'
                for key, values in param_grid.items():
                    pipeline_param_grid[prefix + key] = values
            else:
                pipeline_param_grid = {}
            
            # Perform grid search
            if len(pipeline_param_grid) > 0:
                # Use RandomizedSearchCV for efficiency
                search = RandomizedSearchCV(
                    pipeline,
                    pipeline_param_grid,
                    n_iter=20,  # Limit iterations for speed
                    cv=3,       # Reduce CV folds for speed
                    random_state=42,
                    n_jobs=-1,
                    scoring='accuracy' if problem_type == 'classification' else 'r2'
                )
                
                search.fit(X, y)
                
                # Extract results
                results = {
                    'success': True,
                    'best_params': search.best_params_,
                    'best_score': float(search.best_score_),
                    'best_model': search.best_estimator_,
                    'cv_results': {
                        'mean_test_scores': [float(score) for score in search.cv_results_['mean_test_score']],
                        'std_test_scores': [float(score) for score in search.cv_results_['std_test_score']],
                        'params': [dict(params) for params in search.cv_results_['params']]
                    }
                }
                
                # Remove non-serializable items for response
                response_results = results.copy()
                response_results.pop('best_model', None)
                response_results = self._make_json_serializable(response_results)
                
                return response_results
            else:
                return {'success': False, 'error': 'No parameters to tune'}
            
        except Exception as e:
            logging.error(f"Error in hyperparameter tuning: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _get_default_param_grid(self, model_type, problem_type):
        """Get default parameter grids for hyperparameter tuning"""
        param_grids = {
            'classification': {
                'random_forest': {
                    'n_estimators': [50, 100, 200],
                    'max_depth': [3, 5, 10, None],
                    'min_samples_split': [2, 5, 10],
                    'min_samples_leaf': [1, 2, 4]
                },
                'logistic_regression': {
                    'C': [0.1, 1.0, 10.0],
                    'solver': ['liblinear', 'lbfgs'],
                    'max_iter': [1000]
                },
                'svm': {
                    'C': [0.1, 1, 10],
                    'kernel': ['rbf', 'linear'],
                    'gamma': ['scale', 'auto']
                },
                'gradient_boosting': {
                    'n_estimators': [50, 100, 200],
                    'learning_rate': [0.01, 0.1, 0.2],
                    'max_depth': [3, 5, 7]
                }
            },
            'regression': {
                'random_forest': {
                    'n_estimators': [50, 100, 200],
                    'max_depth': [3, 5, 10, None],
                    'min_samples_split': [2, 5, 10],
                    'min_samples_leaf': [1, 2, 4]
                },
                'ridge': {
                    'alpha': [0.1, 1.0, 10.0, 100.0]
                },
                'lasso': {
                    'alpha': [0.1, 1.0, 10.0, 100.0]
                },
                'gradient_boosting': {
                    'n_estimators': [50, 100, 200],
                    'learning_rate': [0.01, 0.1, 0.2],
                    'max_depth': [3, 5, 7]
                }
            }
        }
        
        return param_grids.get(problem_type, {}).get(model_type, {})
    
    def auto_ml(self, df, target_column, feature_columns=None, problem_type='auto', time_limit=300):
        """Automated Machine Learning - try multiple models and return the best"""
        try:
            # Use all columns except target if no features specified
            if feature_columns is None:
                feature_columns = [col for col in df.columns if col != target_column]
            
            # Preprocess data
            X, y, preprocessor, prep_info = self.preprocess_data(df, target_column, feature_columns)
            
            if X is None:
                return {'success': False, 'error': prep_info.get('error', 'Unknown preprocessing error')}
            
            # Determine problem type if auto
            if problem_type == 'auto':
                problem_type = prep_info['problem_type']
            
            # Select models to try
            if problem_type == 'classification':
                models_to_try = ['random_forest', 'logistic_regression', 'gradient_boosting']
                if HAS_XGB:
                    models_to_try.append('xgboost')
            else:
                models_to_try = ['random_forest', 'linear_regression', 'ridge', 'gradient_boosting']
                if HAS_XGB:
                    models_to_try.append('xgboost')
            
            results = []
            best_score = -np.inf if problem_type == 'regression' else 0
            best_model_info = None
            
            # Try each model
            for model_type in models_to_try:
                try:
                    # Train model
                    model_result = self.train_model(
                        df, target_column, feature_columns, 
                        model_type, problem_type
                    )
                    
                    if model_result['success']:
                        # Get primary metric
                        if problem_type == 'classification':
                            score = model_result['metrics']['accuracy']
                        else:
                            score = model_result['metrics']['r2']
                        
                        model_info = {
                            'model_type': model_type,
                            'score': score,
                            'metrics': model_result['metrics'],
                            'cv_mean': model_result['metrics'].get('cv_mean', 0),
                            'cv_std': model_result['metrics'].get('cv_std', 0)
                        }
                        
                        results.append(model_info)
                        
                        # Check if this is the best model
                        if (problem_type == 'classification' and score > best_score) or \
                           (problem_type == 'regression' and score > best_score):
                            best_score = score
                            best_model_info = model_info
                            best_model_info['full_result'] = model_result
                
                except Exception as e:
                    logging.warning(f"Failed to train {model_type}: {str(e)}")
                    continue
            
            if not results:
                return {'success': False, 'error': 'No models could be trained successfully'}
            
            # Sort results by score
            results.sort(key=lambda x: x['score'], reverse=True)
            
            return {
                'success': True,
                'best_model': best_model_info,
                'all_results': results,
                'problem_type': problem_type,
                'feature_columns': feature_columns,
                'target_column': target_column,
                'summary': {
                    'models_tried': len(results),
                    'best_model_type': best_model_info['model_type'],
                    'best_score': best_score
                }
            }
            
        except Exception as e:
            logging.error(f"Error in auto ML: {str(e)}")
            return {'success': False, 'error': str(e)}
