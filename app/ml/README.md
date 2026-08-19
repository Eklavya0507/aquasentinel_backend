# B1 model artifacts

- `B1_disease_risk_model.pkl`: uploaded sklearn/XGBoost pipeline.
- `B1_label_encoder.pkl`: uploaded label encoder.

The notebook shows B1 uses 30 environmental/demographic inputs and excludes symptoms. It is therefore connected to `/api/ai/environmental-risk/predict`, not to the symptom-assessment UI.

The artifacts were saved with scikit-learn 1.9.0 and XGBoost 3.4.1 according to the notebook/model metadata, so the requirements match those versions.
