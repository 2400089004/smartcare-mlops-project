# UCI Heart Disease dataset

This project includes the processed Cleveland subset from the UCI Machine Learning Repository.

- `heart.csv`: ready-to-use CSV with column headers.
- `processed.cleveland.data`: original processed data file from the UCI archive.
- `prepare_heart.py`: regenerates `heart.csv` from the original file.
- `heart-disease.names`: dataset description from the archive.

Source: https://archive.ics.uci.edu/dataset/45/heart+disease

The dataset contains 303 rows and 14 columns (13 input features plus `num`). Six feature values are missing; they are intentionally kept blank so the training pipeline can impute them. The training script converts the original target `num` into a binary label: 0 = target-negative, values above 0 = target-positive, following a common educational benchmark convention.

Use only for learning and reproducible experimentation. This small, older dataset is not suitable for clinical decisions or claims about real-world diagnostic performance. Do not enter real patient data into this demo.
