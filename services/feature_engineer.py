import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler, LabelEncoder, OneHotEncoder
from sklearn.feature_selection import SelectKBest, f_classif, f_regression, mutual_info_classif, mutual_info_regression
from sklearn.feature_selection import RFE, RFECV, VarianceThreshold, SelectFromModel
from sklearn.decomposition import PCA, TruncatedSVD, FactorAnalysis
from sklearn.cluster import DBSCAN
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LassoCV, RidgeCV
from sklearn.model_selection import cross_val_score
from sklearn.impute import SimpleImputer, KNNImputer
from sklearn.experimental import enable_iterative_imputer  # noqa
from sklearn.impute import IterativeImputer
from scipy import stats
import logging

class FeatureEngineer:
    """Comprehensive feature engineering and preprocessing"""
    
    def __init__(self):
        self.scaler = None
        self.imputer = None
        self.encoder = None
        self.feature_selector = None
        self.pca = None
        
    def handle_missing_values(self, df, strategy='auto', columns=None):
        """
        Comprehensive missing value handling
        
        Args:
            df: DataFrame
            strategy: 'mean', 'median', 'mode', 'constant', 'knn', 'iterative', 'drop', 'auto'
            columns: List of columns to process (None for all)
        """
        try:
            if columns is None:
                columns = df.columns.tolist()
            
            result_df = df.copy()
            strategies_used = {}
            
            for col in columns:
                if col not in df.columns:
                    continue
                    
                missing_count = df[col].isnull().sum()
                if missing_count == 0:
                    strategies_used[col] = 'no_missing'
                    continue
                
                missing_pct = (missing_count / len(df)) * 100
                
                if strategy == 'auto':
                    # Auto-select strategy based on data type and missing percentage
                    if missing_pct > 50:
                        # Too many missing values - consider dropping
                        current_strategy = 'drop_column'
                        result_df = result_df.drop(columns=[col])
                    elif df[col].dtype in ['int64', 'float64']:
                        if missing_pct < 5:
                            current_strategy = 'mean'
                            result_df[col].fillna(df[col].mean(), inplace=True)
                        elif missing_pct < 20:
                            current_strategy = 'median'
                            result_df[col].fillna(df[col].median(), inplace=True)
                        else:
                            current_strategy = 'knn'
                            imputer = KNNImputer(n_neighbors=5)
                            result_df[col] = imputer.fit_transform(result_df[[col]]).ravel()
                    else:
                        # Categorical
                        if missing_pct < 10:
                            current_strategy = 'mode'
                            mode_value = df[col].mode()[0] if not df[col].mode().empty else 'unknown'
                            result_df[col].fillna(mode_value, inplace=True)
                        else:
                            current_strategy = 'constant'
                            result_df[col].fillna('missing', inplace=True)
                else:
                    current_strategy = strategy
                    if strategy == 'mean' and df[col].dtype in ['int64', 'float64']:
                        result_df[col].fillna(df[col].mean(), inplace=True)
                    elif strategy == 'median' and df[col].dtype in ['int64', 'float64']:
                        result_df[col].fillna(df[col].median(), inplace=True)
                    elif strategy == 'mode':
                        mode_value = df[col].mode()[0] if not df[col].mode().empty else 'unknown'
                        result_df[col].fillna(mode_value, inplace=True)
                    elif strategy == 'constant':
                        fill_value = 0 if df[col].dtype in ['int64', 'float64'] else 'missing'
                        result_df[col].fillna(fill_value, inplace=True)
                    elif strategy == 'knn':
                        imputer = KNNImputer(n_neighbors=5)
                        if df[col].dtype in ['int64', 'float64']:
                            result_df[col] = imputer.fit_transform(result_df[[col]]).ravel()
                        else:
                            # For categorical, encode first
                            le = LabelEncoder()
                            encoded = le.fit_transform(df[col].astype(str).fillna('missing'))
                            imputed = imputer.fit_transform(encoded.reshape(-1, 1)).ravel()
                            result_df[col] = le.inverse_transform(imputed.astype(int))
                    elif strategy == 'iterative':
                        imputer = IterativeImputer(random_state=42)
                        if df[col].dtype in ['int64', 'float64']:
                            result_df[col] = imputer.fit_transform(result_df[[col]]).ravel()
                    elif strategy == 'drop':
                        result_df = result_df.dropna(subset=[col])
                
                strategies_used[col] = current_strategy
            
            return {
                'data': result_df,
                'strategies_used': strategies_used,
                'original_shape': df.shape,
                'final_shape': result_df.shape,
                'success': True
            }
            
        except Exception as e:
            logging.error(f"Error in missing value handling: {str(e)}")
            return {'error': str(e), 'success': False}
    
    def remove_outliers(self, df, method='auto', columns=None, threshold=3.0):
        """
        Comprehensive outlier removal
        
        Args:
            df: DataFrame
            method: 'iqr', 'zscore', 'modified_zscore', 'isolation_forest', 'auto'
            columns: Columns to process (None for all numeric)
            threshold: Threshold for outlier detection
        """
        try:
            if columns is None:
                columns = df.select_dtypes(include=['number']).columns.tolist()
            
            result_df = df.copy()
            outliers_removed = {}
            
            for col in columns:
                if col not in df.columns or df[col].dtype not in ['int64', 'float64']:
                    continue
                
                original_count = len(result_df)
                col_data = result_df[col].dropna()
                
                if len(col_data) == 0:
                    continue
                
                if method == 'auto':
                    # Auto-select method based on data distribution
                    skewness = abs(col_data.skew())
                    if skewness > 1:
                        current_method = 'iqr'  # Use IQR for skewed data
                    else:
                        current_method = 'zscore'  # Use Z-score for normal data
                else:
                    current_method = method
                
                if current_method == 'iqr':
                    Q1 = col_data.quantile(0.25)
                    Q3 = col_data.quantile(0.75)
                    IQR = Q3 - Q1
                    lower_bound = Q1 - 1.5 * IQR
                    upper_bound = Q3 + 1.5 * IQR
                    outlier_mask = (result_df[col] < lower_bound) | (result_df[col] > upper_bound)
                    
                elif current_method == 'zscore':
                    z_scores = np.abs(stats.zscore(col_data))
                    outlier_indices = col_data.index[z_scores > threshold]
                    outlier_mask = result_df.index.isin(outlier_indices)
                    
                elif current_method == 'modified_zscore':
                    median = np.median(col_data)
                    mad = np.median(np.abs(col_data - median))
                    modified_z_scores = 0.6745 * (col_data - median) / mad if mad != 0 else np.zeros_like(col_data)
                    outlier_indices = col_data.index[np.abs(modified_z_scores) > threshold]
                    outlier_mask = result_df.index.isin(outlier_indices)
                
                # Remove outliers
                outliers_count = outlier_mask.sum()
                result_df = result_df[~outlier_mask]
                
                outliers_removed[col] = {
                    'method': current_method,
                    'outliers_count': int(outliers_count),
                    'outliers_percentage': float((outliers_count / original_count) * 100)
                }
            
            return {
                'data': result_df,
                'outliers_removed': outliers_removed,
                'original_shape': df.shape,
                'final_shape': result_df.shape,
                'success': True
            }
            
        except Exception as e:
            logging.error(f"Error in outlier removal: {str(e)}")
            return {'error': str(e), 'success': False}
    
    def perform_feature_selection(self, df, target_column, method='auto', k=10, problem_type='auto'):
        """
        Comprehensive feature selection
        
        Args:
            df: DataFrame
            target_column: Target variable column name
            method: 'univariate', 'rfe', 'lasso', 'random_forest', 'mutual_info', 'auto'
            k: Number of features to select
            problem_type: 'classification', 'regression', 'auto'
        """
        try:
            if target_column not in df.columns:
                return {'error': f'Target column {target_column} not found', 'success': False}
            
            # Prepare data
            X = df.drop(columns=[target_column])
            y = df[target_column]
            
            # Auto-detect problem type
            if problem_type == 'auto':
                if y.dtype in ['int64', 'float64'] and y.nunique() > 10:
                    problem_type = 'regression'
                else:
                    problem_type = 'classification'
            
            # Handle categorical variables
            X_processed = X.copy()
            categorical_cols = X.select_dtypes(include=['object', 'category']).columns.tolist()
            
            if categorical_cols:
                for col in categorical_cols:
                    le = LabelEncoder()
                    X_processed[col] = le.fit_transform(X_processed[col].astype(str))
            
            # Select feature selection method
            if method == 'auto':
                if len(X_processed.columns) > 50:
                    method = 'lasso'  # Use Lasso for high-dimensional data
                else:
                    method = 'univariate'  # Use univariate for smaller datasets
            
            selected_features = []
            feature_scores = {}
            
            if method == 'univariate':
                if problem_type == 'classification':
                    selector = SelectKBest(score_func=f_classif, k=min(k, len(X_processed.columns)))
                else:
                    selector = SelectKBest(score_func=f_regression, k=min(k, len(X_processed.columns)))
                
                X_selected = selector.fit_transform(X_processed, y)
                selected_features = X_processed.columns[selector.get_support()].tolist()
                feature_scores = dict(zip(X_processed.columns, selector.scores_))
                
            elif method == 'rfe':
                if problem_type == 'classification':
                    estimator = RandomForestClassifier(n_estimators=50, random_state=42)
                else:
                    estimator = RandomForestRegressor(n_estimators=50, random_state=42)
                
                selector = RFE(estimator, n_features_to_select=min(k, len(X_processed.columns)))
                selector.fit(X_processed, y)
                selected_features = X_processed.columns[selector.support_].tolist()
                feature_scores = dict(zip(X_processed.columns, selector.ranking_))
                
            elif method == 'lasso':
                if problem_type == 'classification':
                    from sklearn.linear_model import LogisticRegressionCV
                    estimator = LogisticRegressionCV(cv=5, random_state=42, max_iter=1000)
                else:
                    estimator = LassoCV(cv=5, random_state=42)
                
                estimator.fit(X_processed, y)
                feature_importance = np.abs(estimator.coef_).flatten()
                top_indices = np.argsort(feature_importance)[-k:]
                selected_features = X_processed.columns[top_indices].tolist()
                feature_scores = dict(zip(X_processed.columns, feature_importance))
                
            elif method == 'random_forest':
                if problem_type == 'classification':
                    estimator = RandomForestClassifier(n_estimators=100, random_state=42)
                else:
                    estimator = RandomForestRegressor(n_estimators=100, random_state=42)
                
                estimator.fit(X_processed, y)
                feature_importance = estimator.feature_importances_
                top_indices = np.argsort(feature_importance)[-k:]
                selected_features = X_processed.columns[top_indices].tolist()
                feature_scores = dict(zip(X_processed.columns, feature_importance))
                
            elif method == 'mutual_info':
                if problem_type == 'classification':
                    mi_scores = mutual_info_classif(X_processed, y, random_state=42)
                else:
                    mi_scores = mutual_info_regression(X_processed, y, random_state=42)
                
                top_indices = np.argsort(mi_scores)[-k:]
                selected_features = X_processed.columns[top_indices].tolist()
                feature_scores = dict(zip(X_processed.columns, mi_scores))
            
            # Create result dataframe with selected features
            result_df = df[selected_features + [target_column]]
            
            return {
                'data': result_df,
                'selected_features': selected_features,
                'feature_scores': feature_scores,
                'method_used': method,
                'problem_type': problem_type,
                'original_features': len(X.columns),
                'selected_count': len(selected_features),
                'success': True
            }
            
        except Exception as e:
            logging.error(f"Error in feature selection: {str(e)}")
            return {'error': str(e), 'success': False}
    
    def perform_pca(self, df, n_components='auto', target_column=None):
        """
        Principal Component Analysis
        
        Args:
            df: DataFrame
            n_components: Number of components or 'auto' for optimal selection
            target_column: Column to exclude from PCA (if any)
        """
        try:
            # Prepare data
            if target_column and target_column in df.columns:
                X = df.drop(columns=[target_column])
                y = df[target_column]
            else:
                X = df.copy()
                y = None
            
            # Select only numeric columns
            numeric_cols = X.select_dtypes(include=['number']).columns.tolist()
            if len(numeric_cols) == 0:
                return {'error': 'No numeric columns found for PCA', 'success': False}
            
            X_numeric = X[numeric_cols]
            
            # Handle missing values
            if X_numeric.isnull().any().any():
                imputer = SimpleImputer(strategy='mean')
                X_numeric = pd.DataFrame(imputer.fit_transform(X_numeric), 
                                      columns=X_numeric.columns, 
                                      index=X_numeric.index)
            
            # Standardize the data
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X_numeric)
            
            # Determine number of components
            if n_components == 'auto':
                # Use elbow method to find optimal number of components
                pca_temp = PCA()
                pca_temp.fit(X_scaled)
                cumsum = np.cumsum(pca_temp.explained_variance_ratio_)
                
                # Find the elbow point (95% variance explained)
                n_components = np.argmax(cumsum >= 0.95) + 1
                n_components = min(n_components, len(numeric_cols), 10)  # Limit to 10 components
            else:
                n_components = min(n_components, len(numeric_cols))
            
            # Perform PCA
            pca = PCA(n_components=n_components)
            X_pca = pca.fit_transform(X_scaled)
            
            # Create result dataframe
            component_names = [f'PC{i+1}' for i in range(n_components)]
            result_df = pd.DataFrame(X_pca, columns=component_names, index=X.index)
            
            # Add target column back if it exists
            if y is not None:
                result_df[target_column] = y
            
            # Create loadings dataframe
            loadings = pd.DataFrame(
                pca.components_.T,
                columns=component_names,
                index=numeric_cols
            )
            
            return {
                'data': result_df,
                'loadings': loadings.to_dict(),
                'explained_variance_ratio': pca.explained_variance_ratio_.tolist(),
                'cumulative_variance_ratio': np.cumsum(pca.explained_variance_ratio_).tolist(),
                'n_components': n_components,
                'original_features': len(numeric_cols),
                'variance_explained': float(np.sum(pca.explained_variance_ratio_)),
                'success': True
            }
            
        except Exception as e:
            logging.error(f"Error in PCA: {str(e)}")
            return {'error': str(e), 'success': False}
    
    def scale_features(self, df, method='standard', columns=None):
        """
        Feature scaling
        
        Args:
            df: DataFrame
            method: 'standard', 'minmax', 'robust'
            columns: Columns to scale (None for all numeric)
        """
        try:
            if columns is None:
                columns = df.select_dtypes(include=['number']).columns.tolist()
            
            result_df = df.copy()
            scaling_info = {}
            
            if method == 'standard':
                scaler = StandardScaler()
            elif method == 'minmax':
                scaler = MinMaxScaler()
            elif method == 'robust':
                scaler = RobustScaler()
            else:
                return {'error': f'Unknown scaling method: {method}', 'success': False}
            
            for col in columns:
                if col in df.columns and df[col].dtype in ['int64', 'float64']:
                    original_values = df[col].values.reshape(-1, 1)
                    scaled_values = scaler.fit_transform(original_values)
                    result_df[col] = scaled_values.flatten()
                    
                    scaling_info[col] = {
                        'method': method,
                        'original_mean': float(df[col].mean()),
                        'original_std': float(df[col].std()),
                        'scaled_mean': float(result_df[col].mean()),
                        'scaled_std': float(result_df[col].std())
                    }
            
            return {
                'data': result_df,
                'scaling_info': scaling_info,
                'method_used': method,
                'success': True
            }
            
        except Exception as e:
            logging.error(f"Error in feature scaling: {str(e)}")
            return {'error': str(e), 'success': False}
    
    def encode_categorical_features(self, df, method='auto', columns=None):
        """
        Encode categorical features
        
        Args:
            df: DataFrame
            method: 'label', 'onehot', 'auto'
            columns: Columns to encode (None for all categorical)
        """
        try:
            if columns is None:
                columns = df.select_dtypes(include=['object', 'category']).columns.tolist()
            
            result_df = df.copy()
            encoding_info = {}
            
            for col in columns:
                if col not in df.columns:
                    continue
                
                unique_count = df[col].nunique()
                
                if method == 'auto':
                    # Auto-select encoding method based on cardinality
                    if unique_count <= 10:
                        current_method = 'onehot'
                    else:
                        current_method = 'label'
                else:
                    current_method = method
                
                if current_method == 'label':
                    le = LabelEncoder()
                    result_df[col] = le.fit_transform(df[col].astype(str))
                    encoding_info[col] = {
                        'method': 'label',
                        'unique_count': unique_count,
                        'classes': le.classes_.tolist()
                    }
                    
                elif current_method == 'onehot':
                    # Create dummy variables
                    dummies = pd.get_dummies(df[col], prefix=col, dummy_na=True)
                    result_df = result_df.drop(columns=[col])
                    result_df = pd.concat([result_df, dummies], axis=1)
                    
                    encoding_info[col] = {
                        'method': 'onehot',
                        'unique_count': unique_count,
                        'new_columns': dummies.columns.tolist()
                    }
            
            return {
                'data': result_df,
                'encoding_info': encoding_info,
                'original_shape': df.shape,
                'final_shape': result_df.shape,
                'success': True
            }
            
        except Exception as e:
            logging.error(f"Error in categorical encoding: {str(e)}")
            return {'error': str(e), 'success': False}
    
    def create_polynomial_features(self, df, degree=2, columns=None, interaction_only=False):
        """Create polynomial features"""
        try:
            from sklearn.preprocessing import PolynomialFeatures
            
            if columns is None:
                columns = df.select_dtypes(include=['number']).columns.tolist()
            
            # Limit to prevent explosion of features
            columns = columns[:5] if len(columns) > 5 else columns
            
            if not columns:
                return {'error': 'No numeric columns found', 'success': False}
            
            X = df[columns]
            other_cols = df.drop(columns=columns)
            
            poly = PolynomialFeatures(degree=degree, interaction_only=interaction_only, include_bias=False)
            X_poly = poly.fit_transform(X)
            
            # Create feature names
            feature_names = poly.get_feature_names_out(columns)
            
            # Create result dataframe
            poly_df = pd.DataFrame(X_poly, columns=feature_names, index=df.index)
            result_df = pd.concat([poly_df, other_cols], axis=1)
            
            return {
                'data': result_df,
                'new_features': feature_names.tolist(),
                'original_features': len(columns),
                'total_features': len(feature_names),
                'degree': degree,
                'success': True
            }
            
        except Exception as e:
            logging.error(f"Error creating polynomial features: {str(e)}")
            return {'error': str(e), 'success': False}
    
    def create_binned_features(self, df, columns=None, n_bins=5, strategy='uniform'):
        """Create binned categorical features from continuous variables"""
        try:
            if columns is None:
                columns = df.select_dtypes(include=['number']).columns.tolist()
            
            result_df = df.copy()
            binning_info = {}
            
            for col in columns:
                if col not in df.columns:
                    continue
                
                try:
                    if strategy == 'uniform':
                        result_df[f'{col}_binned'], bins = pd.cut(df[col], bins=n_bins, retbins=True, labels=False)
                    elif strategy == 'quantile':
                        result_df[f'{col}_binned'], bins = pd.qcut(df[col], q=n_bins, retbins=True, labels=False, duplicates='drop')
                    
                    binning_info[col] = {
                        'strategy': strategy,
                        'n_bins': n_bins,
                        'bins': bins.tolist(),
                        'new_column': f'{col}_binned'
                    }
                    
                except Exception as col_error:
                    logging.warning(f"Could not bin column {col}: {str(col_error)}")
                    continue
            
            return {
                'data': result_df,
                'binning_info': binning_info,
                'success': True
            }
            
        except Exception as e:
            logging.error(f"Error creating binned features: {str(e)}")
            return {'error': str(e), 'success': False}
