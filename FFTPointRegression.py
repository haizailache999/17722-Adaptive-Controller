import numpy as np
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, confusion_matrix, mean_squared_error
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.neural_network import MLPClassifier, MLPRegressor
from xgboost import XGBClassifier
from sklearn.model_selection import cross_val_predict, cross_val_score
#import tensorflow as tf
from sklearn.datasets import make_classification
from sklearn.model_selection import train_test_split
#from skl2onnx import convert_sklearn
#from skl2onnx.common.data_types import FloatTensorType
from skl2onnx import convert_sklearn, to_onnx, wrap_as_onnx_mixin
from onnxruntime import InferenceSession
##from skl2onnx.algebra.onnx_ops import OnnxSub, OnnxDiv
#from skl2onnx.algebra.onnx_operator_mixin import OnnxOperatorMixin
# from create_cnn import *
from sklearn.svm import SVR
import pandas as pd

# FILENAMES
dir6_2 = "ML Data/linreg_1.txt"
dir6_2_labels = "ML Data/linreg_1_labels.txt"

# SELECT FILENAMES FOR ANALYSIS
fileName = dir6_2
labelFileName = dir6_2_labels 

# PARAMETERS
num_labels = 8
files_per_label = 10
rows_per_file = 1
kFoldOrNot = True # True - Kfold cross validation, otherwise do a normal train-test split
kFoldNum = 5
internalSplit = True
stringLabel = False # False - Numerical labels on the confusion matrix figure
floatLabel = False
convertModel = True # Convert trained model to different format for deployment on Android. Don't do this with cross-validation
labelFontsize = 32
textFontsize = 26 #26
splitNum = 10 # Index to split for train-test split

train_indices = []
test_indices = []
total_files = num_labels * files_per_label

def get_feats_from_file(fileName):
    # Read features and labels from file
    X = np.loadtxt(fileName)
    
    if (stringLabel):
        y = np.loadtxt(labelFileName, dtype = str)
    elif (floatLabel):
        y = np.loadtxt(labelFileName) * 10
    else:
        y = np.loadtxt(labelFileName)

    # Reshape 1 column/1 row files 
    if X.ndim == 1:
        X_reshaped = X.reshape(-1, 1)
    else:
        X_reshaped = X

    df = pd.DataFrame(X)
    df['label'] = y
    df['press_no_press_label'] = np.where(df['label'] == 1, 0, 1)  # Label 1 is "no press"

    # Getting train_test_split for the press no press model
    press_no_press_df = df.copy()
    train_press_no_press, test_press_no_press = train_test_split(press_no_press_df)

    # All training data for press_no_press classifier model
    all_press_no_press_x = press_no_press_df.drop(['label', 'press_no_press_label'], axis=1).to_numpy()
    all_press_no_press_y = press_no_press_df['press_no_press_label'].to_numpy()

    # Training and testing split for press_no_press classifier model
    train_press_no_press_x = train_press_no_press.drop(['label', 'press_no_press_label'], axis=1).to_numpy()
    train_press_no_press_y = train_press_no_press['press_no_press_label'].to_numpy()
    test_press_no_press_x = test_press_no_press.drop(['label', 'press_no_press_label'], axis=1).to_numpy()
    test_press_no_press_y = test_press_no_press['press_no_press_label'].to_numpy()

    # Getting train_test_split for the y-axis regression model
    # Exclude label 1 ("no press")
    use_df = df[df['label'] != 1]
    train, test = train_test_split(use_df)

    # All training data for y-axis regression model
    all_x = use_df.drop(['label', 'press_no_press_label'], axis=1).to_numpy()
    all_y = use_df['label'].to_numpy()

    # Training and testing split for y-axis regression model
    train_x = train.drop(['label', 'press_no_press_label'], axis=1).to_numpy()
    train_y = train['label'].to_numpy()
    test_x = test.drop(['label', 'press_no_press_label'], axis=1).to_numpy()
    test_y = test['label'].to_numpy()
    
    return all_x, all_y, train_x, train_y, test_x, test_y, all_press_no_press_x, all_press_no_press_y, train_press_no_press_x, train_press_no_press_y, test_press_no_press_x, test_press_no_press_y

def relabel_data_y(x, y):
    """
    Convert numerical labels to y-coordinate values for regression.
    
    Args:
        x: Feature data
        y: Original numerical labels (1-8, where 1 is "no press")
        
    Returns:
        processed_x: Feature data for samples that need y-coordinate prediction
        processed_y: Y-coordinate values corresponding to labels
        no_press_x: Feature data for all samples
        no_press_y: Binary labels (0 for no press, 1 for press)
    """
    processed_x = []
    processed_y = []
    no_press_x = []
    no_press_y = []
    
    for i in range(len(y)):
        # Add data for press/no-press classification for ALL samples
        no_press_x.append(x[i])
        if y[i] == 1:  # "no press" state
            no_press_y.append(0)  # 0 for "no press"
        else:
            no_press_y.append(1)  # 1 for "press"
            
            # Also add to processed data for regression (only for "press" states)
            processed_x.append(x[i])
            
            # Convert labels 2-8 (excluding 1) to y-coordinate values 
            processed_y.append((y[i]-2)/3-1)
    
    return np.array(processed_x), np.array(processed_y), np.array(no_press_x), np.array(no_press_y)

# Load and preprocess data
all_x, all_y, train_x, train_y, test_x, test_y, all_press_no_press_x, all_press_no_press_y, train_press_no_press_x, train_press_no_press_y, test_press_no_press_x, test_press_no_press_y = get_feats_from_file(fileName)

# Process data for Y model
train_features, train_y_coords, train_no_press_x, train_no_press_y = relabel_data_y(train_x, train_y)
test_features, test_y_coords, test_no_press_x, test_no_press_y = relabel_data_y(test_x, test_y)

# Define models
model_y = SVR()
model_press_no_press = SVC(kernel='linear')

# Train models
model_y.fit(train_features, train_y_coords)
model_press_no_press.fit(train_press_no_press_x, train_press_no_press_y)

# Make predictions
y_pred_y = model_y.predict(test_features)
y_pred_no_press = model_press_no_press.predict(test_press_no_press_x)

# Evaluate models
mse_y = mean_squared_error(test_y_coords, y_pred_y)
accuracy = accuracy_score(test_press_no_press_y, y_pred_no_press)

print(f'Regression MSE: {mse_y}')
print(f'Classification Accuracy for press no press: {accuracy}')

def display_mse(y_true, y_pred):
    mse = mean_squared_error(y_true, y_pred)
    print(f"Mean Squared Error: {mse:.2f}")

    # Plotting the results
    plt.figure(figsize=(10, 6))
    sns.scatterplot(x=y_true, y=y_pred)
    plt.xlabel('True Values')
    plt.ylabel('Predictions')
    plt.title('True Values vs Predictions')
    plt.plot([y_true.min(), y_true.max()], [y_true.min(), y_true.max()], 'r--')  # Diagonal line
    plt.grid()
    plt.show()

def final_train_and_save_model(model, X, y, model_name):
    model.fit(X, y)
    
    if (convertModel):
        # Convert scikit-learn model to ONNX format
        onnx_model = to_onnx(model, X.astype(np.float32), target_opset=12)
        
        # Save the ONNX model
        with open(f"{model_name}.onnx", "wb") as f:
            f.write(onnx_model.SerializeToString())
        
        print(f"Model saved as {model_name}.onnx")
        return onnx_model

def predict_with_onnxruntime(onx, X):
    sess = InferenceSession(onx.SerializeToString(), providers=["CPUExecutionProvider"])
    input_name = sess.get_inputs()[0].name
    res = sess.run(None, {input_name: X.astype(np.float32)})
    return res[0]

# Visualize Y predictions
display_mse(test_y_coords, y_pred_y)

# Train final models on all data
final_y_features, final_y_coords, final_no_press_x, final_no_press_y = relabel_data_y(all_x, all_y)
final_train_and_save_model(model_y, final_y_features, final_y_coords, "y_axis_model")
final_train_and_save_model(model_press_no_press, all_press_no_press_x, all_press_no_press_y, "press_no_press_model")

print("Final models trained and saved.")





'''
should appear in the phone as
prediction  = model_no_press.predict(feats)
if prediction == 'pressed:
    classification = model_y.predict(feats)
'''
