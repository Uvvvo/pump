"""
نماذج الذكاء الاصطناعي للتنبؤ بفشل المضخات
"""

import numpy as np
import pandas as pd
import joblib
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, accuracy_score
import xgboost as xgb
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Tuple, Any
from PyQt6.QtCore import QSize

from config import AI_MODELS_CONFIG, PUMP_CONFIG

class FailurePredictor:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.load_model()
    
    def load_model(self):
        """تحميل النموذج المدرب مسبقاً إذا كان موجوداً"""
        try:
            model_path = AI_MODELS_CONFIG['failure_prediction']['model_path']
            if model_path.exists():
                self.model = joblib.load(model_path)
                self.is_trained = True
                self.logger.info("تم تحميل النموذج المدرب بنجاح")
            else:
                self.logger.info("لم يتم العثور على نموذج مدرب، سيتم إنشاء نموذج جديد")
        except Exception as e:
            self.logger.error(f"خطأ في تحميل النموذج: {e}")
            self.model = xgb.XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42
            )
    
    def generate_training_data(self, num_samples: int = 10000) -> pd.DataFrame:
        """توليد بيانات تدريبية محاكاة"""
        np.random.seed(42)
        
        data = {
            'vibration_x': np.concatenate([
                np.random.normal(2.0, 0.5, num_samples//2),  # وضع طبيعي
                np.random.normal(5.0, 1.5, num_samples//2)   # وضع فاشل
            ]),
            'vibration_y': np.concatenate([
                np.random.normal(2.2, 0.6, num_samples//2),
                np.random.normal(5.5, 1.8, num_samples//2)
            ]),
            'vibration_z': np.concatenate([
                np.random.normal(1.8, 0.4, num_samples//2),
                np.random.normal(4.8, 1.6, num_samples//2)
            ]),
            'temperature': np.concatenate([
                np.random.normal(65, 10, num_samples//2),
                np.random.normal(85, 15, num_samples//2)
            ]),
            'pressure': np.concatenate([
                np.random.normal(150, 20, num_samples//2),
                np.random.normal(120, 40, num_samples//2)
            ]),
            'flow_rate': np.concatenate([
                np.random.normal(100, 15, num_samples//2),
                np.random.normal(60, 25, num_samples//2)
            ]),
            'power_consumption': np.concatenate([
                np.random.normal(75, 10, num_samples//2),
                np.random.normal(95, 20, num_samples//2)
            ]),
            'bearing_temperature': np.concatenate([
                np.random.normal(70, 8, num_samples//2),
                np.random.normal(90, 12, num_samples//2)
            ]),
            'oil_level': np.concatenate([
                np.random.uniform(0.8, 1.0, num_samples//2),
                np.random.uniform(0.1, 0.5, num_samples//2)
            ]),
            'oil_quality': np.concatenate([
                np.random.uniform(0.8, 1.0, num_samples//2),
                np.random.uniform(0.2, 0.6, num_samples//2)
            ]),
            'operating_hours': np.concatenate([
                np.random.uniform(0, 2000, num_samples//2),
                np.random.uniform(1500, 5000, num_samples//2)
            ])
        }
        
        df = pd.DataFrame(data)
        
        # إنشاء المتغير المستهدف (الفشل)
        conditions = (
            (df['vibration_x'] > 4.5) |
            (df['temperature'] > 80) |
            (df['oil_level'] < 0.3) |
            (df['oil_quality'] < 0.5) |
            (df['operating_hours'] > 3000)
        )
        df['failure'] = conditions.astype(int)
        
        return df
    
    def train_model(self):
        """تدريب النموذج على البيانات المحاكاة"""
        try:
            # توليد بيانات التدريب
            training_data = self.generate_training_data()
            
            # تقسيم البيانات
            X = training_data[AI_MODELS_CONFIG['failure_prediction']['features']]
            y = training_data['failure']
            
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # تطبيع البيانات
            X_train_scaled = self.scaler.fit_transform(X_train)
            X_test_scaled = self.scaler.transform(X_test)
            
            # تدريب النموذج
            self.model.fit(X_train_scaled, y_train)
            
            # تقييم النموذج
            y_pred = self.model.predict(X_test_scaled)
            accuracy = accuracy_score(y_test, y_pred)
            
            self.logger.info(f"دقة النموذج: {accuracy:.4f}")
            self.logger.info(classification_report(y_test, y_pred))
            
            # حفظ النموذج
            model_path = AI_MODELS_CONFIG['failure_prediction']['model_path']
            joblib.dump(self.model, model_path)
            self.is_trained = True
            
            self.logger.info("تم تدريب النموذج بنجاح وحفظه")
            
        except Exception as e:
            self.logger.error(f"خطأ في تدريب النموذج: {e}")
    
    def predict_failure(self, sensor_data: Dict[str, float]) -> Dict[str, Any]:
        """التنبؤ باحتمالية الفشل بناءً على بيانات المستشعرات"""
        if not self.is_trained:
            self.train_model()
        
        try:
            # تحضير البيانات للإدخال
            input_features = []
            for feature in AI_MODELS_CONFIG['failure_prediction']['features']:
                input_features.append(sensor_data.get(feature, 0))
            
            # تطبيع البيانات
            input_scaled = self.scaler.transform([input_features])
            
            # التنبؤ
            failure_probability = self.model.predict_proba(input_scaled)[0][1]
            
            # تحديد مستوى الخطورة
            if failure_probability < 0.3:
                risk_level = "منخفض"
                failure_type = "لا يوجد فشل متوقع"
            elif failure_probability < 0.7:
                risk_level = "متوسط"
                failure_type = self._determine_failure_type(sensor_data)
            else:
                risk_level = "مرتفع"
                failure_type = self._determine_failure_type(sensor_data)
            
            # توليد التوصيات
            recommendations = self._generate_recommendations(sensor_data, failure_probability)
            
            return {
                'failure_probability': round(failure_probability, 4),
                'predicted_failure_type': failure_type,
                'confidence': round(min(failure_probability * 1.2, 0.95), 4),
                'risk_level': risk_level,
                'recommendations': recommendations,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            self.logger.error(f"خطأ في التنبؤ: {e}")
            return {
                'failure_probability': 0.0,
                'predicted_failure_type': 'خطأ في التنبؤ',
                'confidence': 0.0,
                'risk_level': 'غير معروف',
                'recommendations': ['فحص النظام'],
                'timestamp': datetime.now()
            }
    
    def _determine_failure_type(self, sensor_data: Dict[str, float]) -> str:
        """تحديد نوع الفشل المحتمل"""
        failures = []
        
        if sensor_data.get('vibration_x', 0) > 5.0:
            failures.append("اهتزاز المحور X")
        if sensor_data.get('vibration_y', 0) > 5.0:
            failures.append("اهتزاز المحور Y")
        if sensor_data.get('vibration_z', 0) > 5.0:
            failures.append("اهتزاز المحور Z")
        if sensor_data.get('temperature', 0) > 80:
            failures.append("ارتفاع درجة الحرارة")
        if sensor_data.get('oil_level', 0) < 0.3:
            failures.append("انخفاض مستوى الزيت")
        if sensor_data.get('oil_quality', 0) < 0.5:
            failures.append("تدهور جودة الزيت")
        if sensor_data.get('bearing_temperature', 0) > 85:
            failures.append("ارتفاع حرارة المحامل")
        
        if failures:
            return "، ".join(failures)
        else:
            return "فشل عام"
    
    def _generate_recommendations(self, sensor_data: Dict[str, float], failure_prob: float) -> List[str]:
        """توليد توصيات بناءً على البيانات والتنبؤ"""
        recommendations = []
        
        if failure_prob > 0.7:
            recommendations.append("إيقاف المضخة فوراً والفحص العاجل")
        elif failure_prob > 0.5:
            recommendations.append("جدولة صيانة عاجلة خلال 24 ساعة")
        elif failure_prob > 0.3:
            recommendations.append("جدولة صيانة وقائية خلال أسبوع")
        
        if sensor_data.get('oil_level', 0) < 0.4:
            recommendations.append("إضافة زيت إلى المستوى المطلوب")
        
        if sensor_data.get('oil_quality', 0) < 0.6:
            recommendations.append("استبدال الزيت")
        
        if sensor_data.get('temperature', 0) > 75:
            recommendations.append("فحص نظام التبريد")
        
        if any(v > 4.5 for v in [sensor_data.get('vibration_x', 0), 
                                sensor_data.get('vibration_y', 0), 
                                sensor_data.get('vibration_z', 0)]):
            recommendations.append("فحص التوازن والمحامل")
        
        if not recommendations:
            recommendations.append("المضخة تعمل بشكل طبيعي - متابعة المراقبة")
        
        return recommendations

class AnomalyDetector:
    def __init__(self):
        self.model = IsolationForest(contamination=0.1, random_state=42)
        self.is_trained = False
        self.logger = logging.getLogger(__name__)
    
    def detect_anomalies(self, sensor_data: pd.DataFrame) -> pd.DataFrame:
        """كشف الشذوذ في بيانات المستشعرات"""
        try:
            if len(sensor_data) < 10:
                return pd.DataFrame()
            
            # تدريب النموذج على البيانات الحالية
            features = sensor_data[AI_MODELS_CONFIG['failure_prediction']['features']].fillna(0)
            self.model.fit(features)
            
            # التنبؤ بالشذوذ
            predictions = self.model.predict(features)
            scores = self.model.decision_function(features)
            
            sensor_data['anomaly'] = predictions == -1
            sensor_data['anomaly_score'] = scores
            
            self.is_trained = True
            return sensor_data
            
        except Exception as e:
            self.logger.error(f"خطأ في كشف الشذوذ: {e}")
            return sensor_data

# إنشاء نسخ عامة من النماذج
failure_predictor = FailurePredictor()
anomaly_detector = AnomalyDetector()