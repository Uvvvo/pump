"""
AI models for iPump
"""

import numpy as np
import pandas as pd
import joblib
import json
from sklearn.ensemble import RandomForestClassifier, IsolationForest, GradientBoostingClassifier
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.preprocessing import StandardScaler, RobustScaler
from sklearn.metrics import classification_report, accuracy_score, precision_score, recall_score, f1_score, confusion_matrix
from sklearn.impute import SimpleImputer
import xgboost as xgb
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Tuple, Any, Optional
import warnings
from pathlib import Path
import sqlite3
from contextlib import contextmanager

from config import AI_MODELS_CONFIG, PUMP_CONFIG

# Setup warnings
warnings.filterwarnings('ignore')

class ModelManager:
    """Model manager for training and prediction operations"""
    
    def __init__(self):
        self.logger = self._setup_logger()
        self.model_history = []
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logging system"""
        logger = logging.getLogger(__name__)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def save_model_metadata(self, model, accuracy: float, features: List[str]):
        """Save model metadata"""
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'accuracy': accuracy,
            'features': features,
            'model_type': type(model).__name__,
            'version': '1.0'
        }
        self.model_history.append(metadata)
        
        # Save to file
        metadata_path = Path('models/model_metadata.json')
        metadata_path.parent.mkdir(exist_ok=True)
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(self.model_history, f, indent=4, ensure_ascii=False)

class DataPreprocessor:
    """Data processor for cleaning and preparation"""
    
    def __init__(self):
        self.scaler = RobustScaler()  # More robust to outliers
        self.imputer = SimpleImputer(strategy='median')
        self.feature_names = []
    
    def preprocess_features(self, df: pd.DataFrame, features: List[str], fit: bool = True) -> np.ndarray:
        """Process features"""
        try:
            # Select only required features
            X = df[features].copy()
            self.feature_names = features
            
            # Handle missing values
            if fit:
                X_imputed = self.imputer.fit_transform(X)
            else:
                X_imputed = self.imputer.transform(X)
            
            # Normalize data
            if fit:
                X_scaled = self.scaler.fit_transform(X_imputed)
            else:
                X_scaled = self.scaler.transform(X_imputed)
            
            return X_scaled
            
        except Exception as e:
            raise Exception(f"Error in data processing: {e}")
    
    def get_feature_importance(self, model) -> Dict[str, float]:
        """Get feature importance"""
        try:
            if hasattr(model, 'feature_importances_'):
                importance_dict = dict(zip(self.feature_names, model.feature_importances_))
                return dict(sorted(importance_dict.items(), key=lambda x: x[1], reverse=True))
            return {}
        except Exception as e:
            logging.warning(f"Cannot get feature importance: {e}")
            return {}

class AdvancedFailurePredictor:
    """Advanced pump failure prediction model"""
    
    def __init__(self):
        self.model_manager = ModelManager()
        self.preprocessor = DataPreprocessor()
        self.model = None
        self.is_trained = False
        self.accuracy = 0.0
        self.feature_importance = {}
        self.model_type = "XGBoost"
        self.load_model()
    
    def load_model(self):
        """Load pre-trained model"""
        try:
            model_path = AI_MODELS_CONFIG['failure_prediction']['model_path']
            preprocessor_path = model_path.parent / 'preprocessor.joblib'
            
            if model_path.exists() and preprocessor_path.exists():
                self.model = joblib.load(model_path)
                self.preprocessor = joblib.load(preprocessor_path)
                self.is_trained = True
                self.model_manager.logger.info("✅ Loaded pre-trained model successfully")
                
                # Load model accuracy from metadata
                metadata_path = Path('models/model_metadata.json')
                if metadata_path.exists():
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        if metadata:
                            self.accuracy = metadata[-1].get('accuracy', 0.0)
            else:
                self._initialize_new_model()
                
        except Exception as e:
            self.model_manager.logger.error(f"❌ Error loading model: {e}")
            self._initialize_new_model()
    
    def _initialize_new_model(self):
        """Initialize new model"""
        self.model = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=8,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            eval_metric='logloss'
        )
        self.model_manager.logger.info("🆕 Created new model")
    
    def load_training_data(self) -> pd.DataFrame:
        """
        Load real training data from the specified CSV file.
        This function replaces the dummy data generation.
        """
        training_file = AI_MODELS_CONFIG['failure_prediction'].get('training_data_file')
        try:
            df = pd.read_csv(training_file)
            self.model_manager.logger.info(f"✅ Loaded training data from {training_file}")
            return df
        except Exception as e:
            self.model_manager.logger.error(f"❌ Error loading training data from {training_file}: {e}")
            return pd.DataFrame()  # Return empty DataFrame if there's an error

    def train_model(self, use_cross_validation: bool = True) -> Dict[str, Any]:
        """Train model with advanced options"""
        try:
            self.model_manager.logger.info("🎓 Starting model training...")
            
            # Load training data
            training_data = self.load_training_data()
            if training_data.empty:
                self.model_manager.logger.error("No training data available. Please upload a valid training data file.")
                return {}
            
            # Split data
            features = AI_MODELS_CONFIG['failure_prediction']['features']
            X = training_data[features]
            y = training_data['failure']
            
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # Process data
            X_train_processed = self.preprocessor.preprocess_features(X_train, features, fit=True)
            X_test_processed = self.preprocessor.preprocess_features(X_test, features, fit=False)
            
            if use_cross_validation:
                # Cross-validation
                cv_scores = cross_val_score(self.model, X_train_processed, y_train, cv=5, scoring='accuracy')
                self.model_manager.logger.info(f"📊 Cross-validation accuracy: {cv_scores.mean():.4f} (±{cv_scores.std():.4f})")
            
            # Train model
            self.model.fit(X_train_processed, y_train)
            
            # Evaluate model
            y_pred = self.model.predict(X_test_processed)
            y_pred_proba = self.model.predict_proba(X_test_processed)[:, 1]
            
            # Calculate multiple metrics
            self.accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred)
            recall = recall_score(y_test, y_pred)
            f1 = f1_score(y_test, y_pred)
            
            self.model_manager.logger.info(f"✅ Model accuracy: {self.accuracy:.4f}")
            self.model_manager.logger.info(f"📈 Precision: {precision:.4f}")
            self.model_manager.logger.info(f"📊 Recall: {recall:.4f}")
            self.model_manager.logger.info(f"🎯 F1-Score: {f1:.4f}")
            
            # Get feature importance
            self.feature_importance = self.preprocessor.get_feature_importance(self.model)
            
            # Save model and preprocessor
            model_path = AI_MODELS_CONFIG['failure_prediction']['model_path']
            model_path.parent.mkdir(parents=True, exist_ok=True)
            
            joblib.dump(self.model, model_path)
            joblib.dump(self.preprocessor, model_path.parent / 'preprocessor.joblib')
            
            # Save metadata
            self.model_manager.save_model_metadata(self.model, self.accuracy, features)
            
            self.is_trained = True
            self.model_manager.logger.info("💾 Model saved successfully")
            
            return {
                'accuracy': self.accuracy,
                'precision': precision,
                'recall': recall,
                'f1_score': f1,
                'feature_importance': self.feature_importance,
                'cv_scores': cv_scores.tolist() if use_cross_validation else []
            }
            
        except Exception as e:
            self.model_manager.logger.error(f"❌ Error in model training: {e}")
            raise
    
    def predict_failure(self, sensor_data: Dict[str, float]) -> Dict[str, Any]:
        """Predict failure probability with advanced error handling"""
        if not self.is_trained:
            self.model_manager.logger.warning("⚠️ Model not trained, auto-training...")
            self.train_model()
        
        try:
            # Check for missing data
            missing_features = []
            input_features = []
            
            for feature in AI_MODELS_CONFIG['failure_prediction']['features']:
                value = sensor_data.get(feature)
                if value is None:
                    missing_features.append(feature)
                    input_features.append(0)  # Default value
                else:
                    input_features.append(float(value))
            
            if missing_features:
                self.model_manager.logger.warning(f"⚠️ Missing data: {missing_features}")
            
            # Prepare data for prediction
            input_df = pd.DataFrame([input_features], columns=AI_MODELS_CONFIG['failure_prediction']['features'])
            input_processed = self.preprocessor.preprocess_features(input_df, AI_MODELS_CONFIG['failure_prediction']['features'], fit=False)
            
            # Prediction
            failure_probability = self.model.predict_proba(input_processed)[0][1]
            prediction = self.model.predict(input_processed)[0]
            
            # Improve risk level determination
            risk_level, risk_color = self._calculate_risk_level(failure_probability, sensor_data)
            
            # Determine failure type
            failure_type = self._determine_failure_type(sensor_data)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(sensor_data, failure_probability, risk_level)
            
            # Suggested maintenance timing
            maintenance_timing = self._suggest_maintenance_timing(failure_probability, sensor_data)
            
            return {
                'failure_probability': round(failure_probability, 4),
                'prediction': int(prediction),
                'predicted_failure_type': failure_type,
                'confidence': round(self._calculate_confidence(failure_probability, sensor_data), 4),
                'risk_level': risk_level,
                'risk_color': risk_color,
                'recommendations': recommendations,
                'maintenance_timing': maintenance_timing,
                'feature_contributions': self._get_feature_contributions(sensor_data),
                'timestamp': datetime.now(),
                'model_accuracy': self.accuracy,
                'missing_features': missing_features
            }
            
        except Exception as e:
            self.model_manager.logger.error(f"❌ Prediction error: {e}")
            return self._get_error_response(str(e))
    
    def _calculate_risk_level(self, probability: float, sensor_data: Dict[str, float]) -> Tuple[str, str]:
        """Calculate risk level with colors"""
        # Additional factors affecting risk level
        critical_factors = 0
        if sensor_data.get('temperature', 0) > 85:
            critical_factors += 1
        if sensor_data.get('oil_level', 0) < 0.2:
            critical_factors += 1
        if sensor_data.get('vibration_x', 0) > 6.0:
            critical_factors += 1
        
        # Adjust risk level based on critical factors
        adjusted_probability = probability + (critical_factors * 0.1)
        
        if adjusted_probability >= 0.8 or critical_factors >= 2:
            return "Critical", "#dc3545"  # Red
        elif adjusted_probability >= 0.6:
            return "High", "#fd7e14"  # Orange
        elif adjusted_probability >= 0.4:
            return "Medium", "#ffc107"  # Yellow
        elif adjusted_probability >= 0.2:
            return "Low", "#20c997"  # Light green
        else:
            return "Normal", "#198754"  # Green
    
    def _calculate_confidence(self, probability: float, sensor_data: Dict[str, float]) -> float:
        """Calculate prediction confidence"""
        base_confidence = probability
        
        # Factors that increase confidence
        if all(key in sensor_data for key in ['temperature', 'vibration_x', 'oil_level']):
            base_confidence *= 1.1
        
        # Factors that decrease confidence
        missing_data = len([v for v in sensor_data.values() if v == 0])
        if missing_data > 3:
            base_confidence *= 0.8
        
        return min(base_confidence, 0.95)
    
    def _determine_failure_type(self, sensor_data: Dict[str, float]) -> str:
        """Determine potential failure type accurately"""
        failure_types = []
        
        # Use dynamic thresholds based on feature importance
        vibration_threshold = 4.5 + (self.feature_importance.get('vibration_x', 0) * 2)
        temperature_threshold = 80 + (self.feature_importance.get('temperature', 0) * 10)
        
        if sensor_data.get('vibration_x', 0) > vibration_threshold:
            failure_types.append("X-axis imbalance")
        if sensor_data.get('vibration_y', 0) > vibration_threshold:
            failure_types.append("Y-axis imbalance")
        if sensor_data.get('vibration_z', 0) > vibration_threshold:
            failure_types.append("Z-axis imbalance")
        if sensor_data.get('temperature', 0) > temperature_threshold:
            failure_types.append("Overheating")
        if sensor_data.get('oil_level', 0) < 0.3:
            failure_types.append("Low oil level")
        if sensor_data.get('oil_quality', 0) < 0.4:
            failure_types.append("Oil contamination")
        if sensor_data.get('bearing_temperature', 0) > 85:
            failure_types.append("Bearing damage")
        if sensor_data.get('flow_rate', 0) < 50:
            failure_types.append("Low efficiency")
        
        return ", ".join(failure_types) if failure_types else "No obvious failures"
    
    def _generate_recommendations(self, sensor_data: Dict[str, float], probability: float, risk_level: str) -> List[str]:
        """Generate intelligent recommendations based on data"""
        recommendations = []
        priority = 1
        
        # Urgent recommendations
        if risk_level in ["Critical", "High"]:
            recommendations.append(f"{priority}. Stop pump immediately and contact technical support")
            priority += 1
        
        if sensor_data.get('oil_level', 0) < 0.2:
            recommendations.append(f"{priority}. Urgent oil addition (level very low)")
            priority += 1
        
        if sensor_data.get('temperature', 0) > 90:
            recommendations.append(f"{priority}. Urgent pump cooling")
            priority += 1
        
        # Preventive recommendations
        if probability > 0.6:
            recommendations.append(f"{priority}. Schedule urgent maintenance within 24 hours")
            priority += 1
        elif probability > 0.4:
            recommendations.append(f"{priority}. Schedule maintenance within 3 days")
            priority += 1
        elif probability > 0.2:
            recommendations.append(f"{priority}. Preventive maintenance within a week")
            priority += 1
        
        if sensor_data.get('oil_quality', 0) < 0.5:
            recommendations.append(f"{priority}. Replace oil at the earliest opportunity")
            priority += 1
        
        if any(v > 4.0 for v in [sensor_data.get('vibration_x', 0), 
                                sensor_data.get('vibration_y', 0), 
                                sensor_data.get('vibration_z', 0)]):
            recommendations.append(f"{priority}. Check balance and bearings")
            priority += 1
        
        if not recommendations:
            recommendations.append("Pump operating normally - continue periodic monitoring")
        
        return recommendations
    
    def _suggest_maintenance_timing(self, probability: float, sensor_data: Dict[str, float]) -> str:
        """Suggest maintenance timing"""
        operating_hours = sensor_data.get('operating_hours', 0)
        
        if probability > 0.7:
            return "Immediate (less than 24 hours)"
        elif probability > 0.5:
            return "Urgent (1-3 days)"
        elif probability > 0.3:
            return "Soon (1 week)"
        elif operating_hours > 3000:
            return "Preventive (monthly)"
        else:
            return "Routine (every 3 months)"
    
    def _get_feature_contributions(self, sensor_data: Dict[str, float]) -> Dict[str, float]:
        """Get feature contributions to prediction"""
        contributions = {}
        try:
            for feature, importance in self.feature_importance.items():
                value = sensor_data.get(feature, 0)
                # Calculate approximate contribution
                contributions[feature] = round(value * importance * 10, 4)
        except Exception:
            pass
        
        return contributions
    
    def _get_error_response(self, error_msg: str) -> Dict[str, Any]:
        """Return structured error response"""
        return {
            'failure_probability': 0.0,
            'prediction': 0,
            'predicted_failure_type': 'Prediction error',
            'confidence': 0.0,
            'risk_level': 'Unknown',
            'risk_color': '#6c757d',
            'recommendations': ['Check AI system', 'Review logs'],
            'maintenance_timing': 'Unspecified',
            'feature_contributions': {},
            'timestamp': datetime.now(),
            'model_accuracy': 0.0,
            'error': error_msg
        }
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            'is_trained': self.is_trained,
            'accuracy': self.accuracy,
            'model_type': self.model_type,
            'feature_importance': self.feature_importance,
            'last_trained': self.model_manager.model_history[-1]['timestamp'] if self.model_manager.model_history else 'Not available',
            'features_count': len(AI_MODELS_CONFIG['failure_prediction']['features'])
        }

class AdvancedAnomalyDetector:
    """Advanced anomaly detector"""
    
    def __init__(self):
        self.detector = IsolationForest(
            contamination=0.1,
            random_state=42,
            n_estimators=100
        )
        self.scaler = RobustScaler()
        self.is_trained = False
        self.logger = logging.getLogger(__name__)
    
    def detect_anomalies(self, sensor_data: pd.DataFrame, sensitivity: float = 0.5) -> pd.DataFrame:
        """Detect anomalies with missing feature logging"""
        try:
            sensor_data = sensor_data.copy()

            # Ensure result columns exist by default
            if 'anomaly' not in sensor_data.columns:
                sensor_data['anomaly'] = False
            if 'anomaly_score' not in sensor_data.columns:
                sensor_data['anomaly_score'] = 0.0
            if 'anomaly_severity' not in sensor_data.columns:
                sensor_data['anomaly_severity'] = 'low'

            if len(sensor_data) < 20:
                self.logger.warning("Insufficient data for anomaly detection")
                return sensor_data

            features = AI_MODELS_CONFIG['failure_prediction']['features']

            # Log missing features
            missing = [f for f in features if f not in sensor_data.columns]
            if missing:
                self.logger.warning(f"⚠️ Missing features for anomaly detection: {missing}")
                # Add columns as NaN to ensure column order later
                for m in missing:
                    sensor_data[m] = np.nan

            # Reindex according to required order and temporarily fill
            X = sensor_data.reindex(columns=features).fillna(method='ffill').fillna(0)

            X_scaled = self.scaler.fit_transform(X)

            scores = self.detector.fit_predict(X_scaled)
            anomaly_scores = self.detector.decision_function(X_scaled)
            
            # Convert results to appropriate format
            norm_scores = (anomaly_scores - np.min(anomaly_scores)) / (np.ptp(anomaly_scores) + 1e-9)

            threshold = np.quantile(norm_scores, 1.0 - sensitivity)
            anomalies = norm_scores > threshold

            sensor_data['anomaly_score'] = norm_scores
            sensor_data['anomaly'] = anomalies
            sensor_data['anomaly_severity'] = np.where(norm_scores > 0.8, 'high',
                                                    np.where(norm_scores > 0.5, 'medium', 'low'))

            return sensor_data

        except Exception as e:
            self.logger.error(f"Error in anomaly detection: {e}")
            # Ensure required columns are returned
            if 'anomaly' not in sensor_data.columns:
                sensor_data['anomaly'] = False
            if 'anomaly_score' not in sensor_data.columns:
                sensor_data['anomaly_score'] = 0.0
            if 'anomaly_severity' not in sensor_data.columns:
                sensor_data['anomaly_severity'] = 'low'
            return sensor_data

# Create global instances of advanced models
failure_predictor = AdvancedFailurePredictor()
anomaly_detector = AdvancedAnomalyDetector()