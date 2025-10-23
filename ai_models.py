"""
نماذج الذكاء الاصطناعي للتنبؤ بفشل المضخات
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

# إعداد التحذيرات
warnings.filterwarnings('ignore')

class ModelManager:
    """مدير النماذج للتحكم في عمليات التدريب والتنبؤ"""
    
    def __init__(self):
        self.logger = self._setup_logger()
        self.model_history = []
    
    def _setup_logger(self) -> logging.Logger:
        """إعداد نظام التسجيل"""
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
        """حفظ بيانات وصفية عن النموذج"""
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'accuracy': accuracy,
            'features': features,
            'model_type': type(model).__name__,
            'version': '1.0'
        }
        self.model_history.append(metadata)
        
        # حفظ في ملف
        metadata_path = Path('models/model_metadata.json')
        metadata_path.parent.mkdir(exist_ok=True)
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(self.model_history, f, indent=4, ensure_ascii=False)

class DataPreprocessor:
    """معالج البيانات للتنظيف والتحضير"""
    
    def __init__(self):
        self.scaler = RobustScaler()  # أكثر مقاومة للقيم الشاذة
        self.imputer = SimpleImputer(strategy='median')
        self.feature_names = []
    
    def preprocess_features(self, df: pd.DataFrame, features: List[str], fit: bool = True) -> np.ndarray:
        """معالجة الميزات"""
        try:
            # اختيار الميزات المطلوبة فقط
            X = df[features].copy()
            self.feature_names = features
            
            # معالجة القيم المفقودة
            if fit:
                X_imputed = self.imputer.fit_transform(X)
            else:
                X_imputed = self.imputer.transform(X)
            
            # تطبيع البيانات
            if fit:
                X_scaled = self.scaler.fit_transform(X_imputed)
            else:
                X_scaled = self.scaler.transform(X_imputed)
            
            return X_scaled
            
        except Exception as e:
            raise Exception(f"خطأ في معالجة البيانات: {e}")
    
    def get_feature_importance(self, model) -> Dict[str, float]:
        """الحصول على أهمية الميزات"""
        try:
            if hasattr(model, 'feature_importances_'):
                importance_dict = dict(zip(self.feature_names, model.feature_importances_))
                return dict(sorted(importance_dict.items(), key=lambda x: x[1], reverse=True))
            return {}
        except Exception as e:
            logging.warning(f"لا يمكن الحصول على أهمية الميزات: {e}")
            return {}

class AdvancedFailurePredictor:
    """نموذج متقدم للتنبؤ بفشل المضخات"""
    
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
        """تحميل النموذج المدرب مسبقاً"""
        try:
            model_path = AI_MODELS_CONFIG['failure_prediction']['model_path']
            preprocessor_path = model_path.parent / 'preprocessor.joblib'
            
            if model_path.exists() and preprocessor_path.exists():
                self.model = joblib.load(model_path)
                self.preprocessor = joblib.load(preprocessor_path)
                self.is_trained = True
                self.model_manager.logger.info("✅ تم تحميل النموذج المدرب بنجاح")
                
                # تحميل دقة النموذج من البيانات الوصفية
                metadata_path = Path('models/model_metadata.json')
                if metadata_path.exists():
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        if metadata:
                            self.accuracy = metadata[-1].get('accuracy', 0.0)
            else:
                self._initialize_new_model()
                
        except Exception as e:
            self.model_manager.logger.error(f"❌ خطأ في تحميل النموذج: {e}")
            self._initialize_new_model()
    
    def _initialize_new_model(self):
        """تهيئة نموذج جديد"""
        self.model = xgb.XGBClassifier(
            n_estimators=200,
            max_depth=8,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            eval_metric='logloss'
        )
        self.model_manager.logger.info("🆕 تم إنشاء نموذج جديد")
    
    def generate_training_data(self, num_samples: int = 15000) -> pd.DataFrame:
        """توليد بيانات تدريبية محاكاة أكثر واقعية"""
        np.random.seed(42)
        
        # بيانات أكثر واقعية مع علاقات بين المتغيرات
        operating_hours = np.random.exponential(2000, num_samples)
        
        data = {
            'vibration_x': self._generate_vibration_data(operating_hours, num_samples, base=2.0),
            'vibration_y': self._generate_vibration_data(operating_hours, num_samples, base=2.2),
            'vibration_z': self._generate_vibration_data(operating_hours, num_samples, base=1.8),
            'temperature': self._generate_temperature_data(operating_hours, num_samples),
            'pressure': self._generate_pressure_data(operating_hours, num_samples),
            'flow_rate': self._generate_flow_rate_data(operating_hours, num_samples),
            'power_consumption': self._generate_power_data(operating_hours, num_samples),
            'bearing_temperature': self._generate_bearing_temperature(operating_hours, num_samples),
            'oil_level': self._generate_oil_level_data(operating_hours, num_samples),
            'oil_quality': self._generate_oil_quality_data(operating_hours, num_samples),
            'operating_hours': operating_hours,
            'maintenance_due': np.random.choice([0, 1], num_samples, p=[0.7, 0.3])
        }
        
        df = pd.DataFrame(data)
        
        # إنشاء المتغير المستهدف (الفشل) مع منطق أكثر تعقيداً
        df['failure'] = self._calculate_failure_risk(df)
        
        return df
    
    def _generate_vibration_data(self, operating_hours: np.ndarray, num_samples: int, base: float) -> np.ndarray:
        """توليد بيانات اهتزاز واقعية"""
        vibration = np.zeros(num_samples)
        for i, hours in enumerate(operating_hours):
            if hours > 4000:  # مضخة قديمة
                vibration[i] = np.random.normal(base * 2.5, 1.0)
            elif hours > 2000:  # مضخة متوسطة العمر
                vibration[i] = np.random.normal(base * 1.5, 0.7)
            else:  # مضخة جديدة
                vibration[i] = np.random.normal(base, 0.3)
        return np.clip(vibration, 0, 10)
    
    def _generate_temperature_data(self, operating_hours: np.ndarray, num_samples: int) -> np.ndarray:
        """توليد بيانات درجة حرارة واقعية"""
        temperature = np.zeros(num_samples)
        for i, hours in enumerate(operating_hours):
            base_temp = 60 + (hours / 5000) * 30  # زيادة الحرارة مع العمر
            temperature[i] = np.random.normal(base_temp, 8)
        return np.clip(temperature, 40, 120)
    
    def _generate_pressure_data(self, operating_hours: np.ndarray, num_samples: int) -> np.ndarray:
        """توليد بيانات ضغط واقعية"""
        pressure = np.zeros(num_samples)
        for i, hours in enumerate(operating_hours):
            if hours > 3000:
                pressure[i] = np.random.normal(130, 35)  # ضغط منخفض للمضخات القديمة
            else:
                pressure[i] = np.random.normal(150, 20)
        return np.clip(pressure, 50, 250)
    
    def _generate_flow_rate_data(self, operating_hours: np.ndarray, num_samples: int) -> np.ndarray:
        """توليد بيانات معدل تدفق واقعية"""
        flow_rate = np.zeros(num_samples)
        for i, hours in enumerate(operating_hours):
            if hours > 3500:
                flow_rate[i] = np.random.normal(70, 30)  # تدفق أقل للمضخات القديمة
            else:
                flow_rate[i] = np.random.normal(100, 15)
        return np.clip(flow_rate, 20, 150)
    
    def _generate_power_data(self, operating_hours: np.ndarray, num_samples: int) -> np.ndarray:
        """توليد بيانات استهلاك طاقة واقعية"""
        power = np.zeros(num_samples)
        for i, hours in enumerate(operating_hours):
            base_power = 70 + (hours / 5000) * 25  # زيادة استهلاك الطاقة مع العمر
            power[i] = np.random.normal(base_power, 12)
        return np.clip(power, 50, 150)
    
    def _generate_bearing_temperature(self, operating_hours: np.ndarray, num_samples: int) -> np.ndarray:
        """توليد بيانات حرارة المحامل واقعية"""
        bearing_temp = np.zeros(num_samples)
        for i, hours in enumerate(operating_hours):
            base_temp = 65 + (hours / 5000) * 25  # زيادة حرارة المحامل مع العمر
            bearing_temp[i] = np.random.normal(base_temp, 10)
        return np.clip(bearing_temp, 50, 110)
    
    def _generate_oil_level_data(self, operating_hours: np.ndarray, num_samples: int) -> np.ndarray:
        """توليد بيانات مستوى الزيت واقعية"""
        oil_level = np.zeros(num_samples)
        for i, hours in enumerate(operating_hours):
            if hours > 2500:
                oil_level[i] = np.random.uniform(0.2, 0.7)  # مستوى زيت منخفض للمضخات القديمة
            else:
                oil_level[i] = np.random.uniform(0.6, 1.0)
        return np.clip(oil_level, 0.1, 1.0)
    
    def _generate_oil_quality_data(self, operating_hours: np.ndarray, num_samples: int) -> np.ndarray:
        """توليد بيانات جودة الزيت واقعية"""
        oil_quality = np.zeros(num_samples)
        for i, hours in enumerate(operating_hours):
            base_quality = 0.9 - (hours / 10000)  # تدهور جودة الزيت مع الوقت
            oil_quality[i] = np.random.uniform(max(0.1, base_quality - 0.2), base_quality)
        return np.clip(oil_quality, 0.1, 1.0)
    
    def _calculate_failure_risk(self, df: pd.DataFrame) -> np.ndarray:
        """حساب خطر الفشل بناءً على متعددة معايير"""
        risk_score = (
            (df['vibration_x'] > 4.0).astype(int) * 0.15 +
            (df['vibration_y'] > 4.0).astype(int) * 0.15 +
            (df['vibration_z'] > 4.0).astype(int) * 0.15 +
            (df['temperature'] > 80).astype(int) * 0.2 +
            (df['oil_level'] < 0.3).astype(int) * 0.15 +
            (df['oil_quality'] < 0.4).astype(int) * 0.1 +
            (df['bearing_temperature'] > 85).astype(int) * 0.1
        )
        
        # تحويل درجة الخطر إلى توقع فشل (0 أو 1)
        failure = (risk_score > 0.3).astype(int)
        return failure
    
    def train_model(self, use_cross_validation: bool = True) -> Dict[str, Any]:
        """تدريب النموذج مع خيارات متقدمة"""
        try:
            self.model_manager.logger.info("🎓 بدء تدريب النموذج...")
            
            # توليد بيانات التدريب
            training_data = self.generate_training_data()
            
            # تقسيم البيانات
            features = AI_MODELS_CONFIG['failure_prediction']['features']
            X = training_data[features]
            y = training_data['failure']
            
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            # معالجة البيانات
            X_train_processed = self.preprocessor.preprocess_features(X_train, features, fit=True)
            X_test_processed = self.preprocessor.preprocess_features(X_test, features, fit=False)
            
            if use_cross_validation:
                # التحقق المتبادل
                cv_scores = cross_val_score(self.model, X_train_processed, y_train, cv=5, scoring='accuracy')
                self.model_manager.logger.info(f"📊 دقة التحقق المتبادل: {cv_scores.mean():.4f} (±{cv_scores.std():.4f})")
            
            # تدريب النموذج
            self.model.fit(X_train_processed, y_train)
            
            # تقييم النموذج
            y_pred = self.model.predict(X_test_processed)
            y_pred_proba = self.model.predict_proba(X_test_processed)[:, 1]
            
            # حساب مقاييس متعددة
            self.accuracy = accuracy_score(y_test, y_pred)
            precision = precision_score(y_test, y_pred)
            recall = recall_score(y_test, y_pred)
            f1 = f1_score(y_test, y_pred)
            
            self.model_manager.logger.info(f"✅ دقة النموذج: {self.accuracy:.4f}")
            self.model_manager.logger.info(f"📈 الدقة (Precision): {precision:.4f}")
            self.model_manager.logger.info(f"📊 الاستدعاء (Recall): {recall:.4f}")
            self.model_manager.logger.info(f"🎯 F1-Score: {f1:.4f}")
            
            # الحصول على أهمية الميزات
            self.feature_importance = self.preprocessor.get_feature_importance(self.model)
            
            # حفظ النموذج والمعالج
            model_path = AI_MODELS_CONFIG['failure_prediction']['model_path']
            model_path.parent.mkdir(parents=True, exist_ok=True)
            
            joblib.dump(self.model, model_path)
            joblib.dump(self.preprocessor, model_path.parent / 'preprocessor.joblib')
            
            # حفظ البيانات الوصفية
            self.model_manager.save_model_metadata(self.model, self.accuracy, features)
            
            self.is_trained = True
            self.model_manager.logger.info("💾 تم حفظ النموذج بنجاح")
            
            return {
                'accuracy': self.accuracy,
                'precision': precision,
                'recall': recall,
                'f1_score': f1,
                'feature_importance': self.feature_importance,
                'cv_scores': cv_scores.tolist() if use_cross_validation else []
            }
            
        except Exception as e:
            self.model_manager.logger.error(f"❌ خطأ في تدريب النموذج: {e}")
            raise
    
    def predict_failure(self, sensor_data: Dict[str, float]) -> Dict[str, Any]:
        """التنبؤ باحتمالية الفشل مع معالجة متقدمة للأخطاء"""
        if not self.is_trained:
            self.model_manager.logger.warning("⚠️ النموذج غير مدرب، جاري التدريب التلقائي...")
            self.train_model()
        
        try:
            # التحقق من البيانات المفقودة
            missing_features = []
            input_features = []
            
            for feature in AI_MODELS_CONFIG['failure_prediction']['features']:
                value = sensor_data.get(feature)
                if value is None:
                    missing_features.append(feature)
                    input_features.append(0)  # قيمة افتراضية
                else:
                    input_features.append(float(value))
            
            if missing_features:
                self.model_manager.logger.warning(f"⚠️ بيانات مفقودة: {missing_features}")
            
            # تحضير البيانات للتنبؤ
            input_df = pd.DataFrame([input_features], columns=AI_MODELS_CONFIG['failure_prediction']['features'])
            input_processed = self.preprocessor.preprocess_features(input_df, AI_MODELS_CONFIG['failure_prediction']['features'], fit=False)
            
            # التنبؤ
            failure_probability = self.model.predict_proba(input_processed)[0][1]
            prediction = self.model.predict(input_processed)[0]
            
            # تحسين تحديد مستوى الخطورة
            risk_level, risk_color = self._calculate_risk_level(failure_probability, sensor_data)
            
            # تحديد نوع الفشل
            failure_type = self._determine_failure_type(sensor_data)
            
            # توليد التوصيات
            recommendations = self._generate_recommendations(sensor_data, failure_probability, risk_level)
            
            # وقت الصيانة المقترح
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
            self.model_manager.logger.error(f"❌ خطأ في التنبؤ: {e}")
            return self._get_error_response(str(e))
    
    def _calculate_risk_level(self, probability: float, sensor_data: Dict[str, float]) -> Tuple[str, str]:
        """حساب مستوى الخطورة مع ألوان"""
        # عوامل إضافية تؤثر على مستوى الخطورة
        critical_factors = 0
        if sensor_data.get('temperature', 0) > 85:
            critical_factors += 1
        if sensor_data.get('oil_level', 0) < 0.2:
            critical_factors += 1
        if sensor_data.get('vibration_x', 0) > 6.0:
            critical_factors += 1
        
        # تعديل مستوى الخطورة بناءً على العوامل الحرجة
        adjusted_probability = probability + (critical_factors * 0.1)
        
        if adjusted_probability >= 0.8 or critical_factors >= 2:
            return "حرج", "#dc3545"  # أحمر
        elif adjusted_probability >= 0.6:
            return "مرتفع", "#fd7e14"  # برتقالي
        elif adjusted_probability >= 0.4:
            return "متوسط", "#ffc107"  # أصفر
        elif adjusted_probability >= 0.2:
            return "منخفض", "#20c997"  # أخضر فاتح
        else:
            return "طبيعي", "#198754"  # أخضر
    
    def _calculate_confidence(self, probability: float, sensor_data: Dict[str, float]) -> float:
        """حساب ثقة التنبؤ"""
        base_confidence = probability
        
        # عوامل تزيد الثقة
        if all(key in sensor_data for key in ['temperature', 'vibration_x', 'oil_level']):
            base_confidence *= 1.1
        
        # عوامل تقلل الثقة
        missing_data = len([v for v in sensor_data.values() if v == 0])
        if missing_data > 3:
            base_confidence *= 0.8
        
        return min(base_confidence, 0.95)
    
    def _determine_failure_type(self, sensor_data: Dict[str, float]) -> str:
        """تحديد نوع الفشل المحتمل بدقة"""
        failure_types = []
        
        # استخدام عتبات ديناميكية بناءً على أهمية الميزات
        vibration_threshold = 4.5 + (self.feature_importance.get('vibration_x', 0) * 2)
        temperature_threshold = 80 + (self.feature_importance.get('temperature', 0) * 10)
        
        if sensor_data.get('vibration_x', 0) > vibration_threshold:
            failure_types.append("عدم اتزان المحور X")
        if sensor_data.get('vibration_y', 0) > vibration_threshold:
            failure_types.append("عدم اتزان المحور Y")
        if sensor_data.get('vibration_z', 0) > vibration_threshold:
            failure_types.append("عدم اتزان المحور Z")
        if sensor_data.get('temperature', 0) > temperature_threshold:
            failure_types.append("ارتفاع درجة الحرارة")
        if sensor_data.get('oil_level', 0) < 0.3:
            failure_types.append("نقص الزيت")
        if sensor_data.get('oil_quality', 0) < 0.4:
            failure_types.append("تلوث الزيت")
        if sensor_data.get('bearing_temperature', 0) > 85:
            failure_types.append("تلف المحامل")
        if sensor_data.get('flow_rate', 0) < 50:
            failure_types.append("انخفاض الكفاءة")
        
        return "، ".join(failure_types) if failure_types else "لا توجد أعطال واضحة"
    
    def _generate_recommendations(self, sensor_data: Dict[str, float], probability: float, risk_level: str) -> List[str]:
        """توليد توصيات ذكية بناءً على البيانات"""
        recommendations = []
        priority = 1
        
        # توصيات عاجلة
        if risk_level in ["حرج", "مرتفع"]:
            recommendations.append(f"{priority}. إيقاف المضخة فوراً والاتصال بالدعم الفني")
            priority += 1
        
        if sensor_data.get('oil_level', 0) < 0.2:
            recommendations.append(f"{priority}. إضافة زيت عاجل (المستوى منخفض جداً)")
            priority += 1
        
        if sensor_data.get('temperature', 0) > 90:
            recommendations.append(f"{priority}. تبريد عاجل للمضخة")
            priority += 1
        
        # توصيات وقائية
        if probability > 0.6:
            recommendations.append(f"{priority}. جدولة صيانة عاجلة خلال 24 ساعة")
            priority += 1
        elif probability > 0.4:
            recommendations.append(f"{priority}. جدولة صيانة خلال 3 أيام")
            priority += 1
        elif probability > 0.2:
            recommendations.append(f"{priority}. صيانة وقائية خلال أسبوع")
            priority += 1
        
        if sensor_data.get('oil_quality', 0) < 0.5:
            recommendations.append(f"{priority}. استبدال الزيت في أقرب فرصة")
            priority += 1
        
        if any(v > 4.0 for v in [sensor_data.get('vibration_x', 0), 
                                sensor_data.get('vibration_y', 0), 
                                sensor_data.get('vibration_z', 0)]):
            recommendations.append(f"{priority}. فحص التوازن والمحامل")
            priority += 1
        
        if not recommendations:
            recommendations.append("المضخة تعمل بشكل طبيعي - متابعة المراقبة الدورية")
        
        return recommendations
    
    def _suggest_maintenance_timing(self, probability: float, sensor_data: Dict[str, float]) -> str:
        """اقتراح توقيت الصيانة"""
        operating_hours = sensor_data.get('operating_hours', 0)
        
        if probability > 0.7:
            return "فوري (أقل من 24 ساعة)"
        elif probability > 0.5:
            return "عاجل (1-3 أيام)"
        elif probability > 0.3:
            return "قريب (أسبوع)"
        elif operating_hours > 3000:
            return "وقائي (شهري)"
        else:
            return "روتيني (كل 3 أشهر)"
    
    def _get_feature_contributions(self, sensor_data: Dict[str, float]) -> Dict[str, float]:
        """الحصول على مساهمة كل ميزة في التنبؤ"""
        contributions = {}
        try:
            for feature, importance in self.feature_importance.items():
                value = sensor_data.get(feature, 0)
                # حساب مساهمة تقريبية (يمكن تحسين هذا المنطق)
                contributions[feature] = round(value * importance * 10, 4)
        except Exception:
            pass
        
        return contributions
    
    def _get_error_response(self, error_msg: str) -> Dict[str, Any]:
        """إرجاع رد خطأ منظم"""
        return {
            'failure_probability': 0.0,
            'prediction': 0,
            'predicted_failure_type': 'خطأ في التنبؤ',
            'confidence': 0.0,
            'risk_level': 'غير معروف',
            'risk_color': '#6c757d',
            'recommendations': ['فحص نظام الذكاء الاصطناعي', 'مراجعة السجلات'],
            'maintenance_timing': 'غير محدد',
            'feature_contributions': {},
            'timestamp': datetime.now(),
            'model_accuracy': 0.0,
            'error': error_msg
        }
    
    def get_model_info(self) -> Dict[str, Any]:
        """الحصول على معلومات النموذج"""
        return {
            'is_trained': self.is_trained,
            'accuracy': self.accuracy,
            'model_type': self.model_type,
            'feature_importance': self.feature_importance,
            'last_trained': self.model_manager.model_history[-1]['timestamp'] if self.model_manager.model_history else 'غير متوفر',
            'features_count': len(AI_MODELS_CONFIG['failure_prediction']['features'])
        }

class AdvancedAnomalyDetector:
    """كاشف شذوذ متقدم"""
    
    def __init__(self):
        self.model = IsolationForest(
            contamination=0.1,
            random_state=42,
            n_estimators=100
        )
        self.scaler = RobustScaler()
        self.is_trained = False
        self.logger = logging.getLogger(__name__)
    
    def detect_anomalies(self, sensor_data: pd.DataFrame, sensitivity: float = 0.5) -> pd.DataFrame:
        """كشف الشذوذ مع قابلية ضبط الحساسية"""
        try:
            if len(sensor_data) < 20:
                self.logger.warning("بيانات غير كافية لكشف الشذوذ")
                sensor_data['anomaly'] = False
                sensor_data['anomaly_score'] = 0.0
                sensor_data['anomaly_severity'] = 'low'
                return sensor_data
            
            # معالجة البيانات
            features = AI_MODELS_CONFIG['failure_prediction']['features']
            X = sensor_data[features].fillna(method='ffill').fillna(0)
            X_scaled = self.scaler.fit_transform(X)
            
            # ضبط الحساسية
            contamination = 0.05 + (sensitivity * 0.1)  # 0.05 إلى 0.15
            self.model.set_params(contamination=min(contamination, 0.2))
            
            # الكشف عن الشذوذ
            anomalies = self.model.fit_predict(X_scaled)
            scores = self.model.decision_function(X_scaled)
            
            # إضافة النتائج للبيانات
            sensor_data['anomaly'] = anomalies == -1
            sensor_data['anomaly_score'] = scores
            sensor_data['anomaly_severity'] = sensor_data['anomaly_score'].apply(
                lambda x: 'high' if x < -0.1 else 'medium' if x < 0 else 'low'
            )
            
            self.is_trained = True
            
            # تسجيل الإحصائيات
            anomaly_count = sensor_data['anomaly'].sum()
            self.logger.info(f"تم كشف {anomaly_count} حالة شذوذ من {len(sensor_data)} سجل")
            
            return sensor_data
            
        except Exception as e:
            self.logger.error(f"خطأ في كشف الشذوذ: {e}")
            return sensor_data

# إنشاء نسخ عامة من النماذج المطورة
failure_predictor = AdvancedFailurePredictor()
anomaly_detector = AdvancedAnomalyDetector()