# -*- coding: utf-8 -*-
"""forecasting.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/gist/LhuiOSU/bd6e93d0f3444e85855bd575bf278798/forecasting.ipynb
"""

#@title Enter the symbol, hold length, and lookback:
from ast import literal_eval
import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math as m
import random
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cross_validation import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score
from sklearn.metrics import f1_score
from sklearn import tree
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import classification_report,confusion_matrix
from sklearn import svm
from sklearn import model_selection
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression

asset = "ETH" #@param {type:"string"}
hold = 5 #@param {type:"integer"}
look_back = 20 #@param {type:"integer"}

"""$\Huge\text{We scrape the data for (ASSET)/USD from an API: }$"""

import requests
import datetime
import pandas as pd
import matplotlib.pyplot as plt

def minute_price_historical(symbol, comparison_symbol, limit, aggregate, exchange=''):
    url = 'https://min-api.cryptocompare.com/data/histominute?fsym={}&tsym={}&limit={}&aggregate={}'\
            .format(symbol.upper(), comparison_symbol.upper(), limit, aggregate)
    if exchange:
        url += '&e={}'.format(exchange)
    page = requests.get(url)
    data = page.json()['Data']
    df = pd.DataFrame(data)
    df['timestamp'] = [datetime.datetime.fromtimestamp(d) for d in df.time]
    return df



#note this dataset is top down, so the earliest date is the first column

ETHMinute = minute_price_historical(asset, 'USD', 2000, 1)
#ETHMinute['time'] = pd.to_datetime(ETHMinute['time'],unit='s')

#The function "createTrain" is deprecated, I've decided it's not the best way to
#create the training set. Best to actually use time steps which I will implement
#below. 

#ETHMinute = createTrain(ETHMinute, 20)

#we drop the timestamp column since it isn't a number and we want to convert to
#floating point values in the next code block. 

ETHMinute = ETHMinute.drop(columns=['timestamp'])

rawDataCopy = ETHMinute.copy()

print(ETHMinute.iloc[0])

#ETHMinute.head(1)

"""#We perform some exploratory data analysis:"""

#Do an in-depth exporatory data analysis, discussing trends, correlations, anomalies, 
#and anything else we discussed in class for EDA

#Don't use ETHMinute, it will mess up ALL of the rest of the code
#A copy has been made, yeah

#Analysis the head 10 dataset as an example.
#correlation about the low price and selling volume of each set

low = []
volume_diff= []
close = []

#print(rawDataCopy.iloc[1][2])
for i in range(200):
  close.append(rawDataCopy.iloc[i][0])

for i in range(200):
  low.append(rawDataCopy.iloc[i][2])

for i in range(200):
  volume_diff.append(rawDataCopy.iloc[i][6]-rawDataCopy.iloc[i][5])
# correlation between low price and volume difference and make the graph
print(np.corrcoef(low, volume_diff))
plt.figure()
plt.plot(low, volume_diff, 'ro')

# correlation between close price and volume difference and make the graph
print(np.corrcoef(close, volume_diff))
plt.figure()
plt.plot(close, volume_diff, 'ro')

#df = pd.DataFrame(data=np.column_stack((low,volume_diff)),columns=['low','volume_diff'])
#clf = svm.OneClassSVM(nu=0.05, kernel="rbf", gamma=0.1)
#clf.fit(df)

#pred = clf.predict(df)

# inliers are labeled 1, outliers are labeled -1
#normal = df[pred == 1]
#abnormal = df[pred == -1]

#print(normal)

#plt.figure()


#plt.scatter(normal[0],abnormal[1], color = 'red')
#plt.scatter(abnormal[0],abnormal[1],color= 'blue')
#plt.xlabel('price')
#plt.ylabel('volume')
#plt.show()

#Use only the DataFrame "rawDataCopy":
rawDataCopy.head(10)

"""# We normalize the dataset, applying a min max scaler, and split it into training and test sets. We also reshape the dataset by making look_back copies of the dataset and offsetting them so that we create time series rows."""

from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
from keras.layers import GRU
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error
import scipy

np.random.seed(11)
eth = ETHMinute.values
eth = eth.astype('float32')

classDF = ETHMinute

# We scale the dataset
scaler = MinMaxScaler(feature_range=(0, 1))
eth = scaler.fit_transform(eth)

# We split into train and test sets
train_size = int(len(eth) * 0.67)
test_size = len(eth) - train_size
train, test = eth[0:train_size,:], eth[train_size:len(eth),:]



# We design a function to create a dataset with a fixed number of 
# previous time steps for numpy arrays
def constructTimeSeries(rawData, look_back):
  
  setX = []
  setY = []
  
  for i in range(len(rawData)-look_back-hold):
    
    #this collects a subset of all the columns, from i to i + look_back
		tempSet = rawData[i:(i+look_back), :]
    
		setX.append(tempSet)
		setY.append(rawData[i + look_back + hold - 1, :])
    
  return np.array(setX), np.array(setY)

trainX, trainY = constructTimeSeries(train, look_back)
testX, testY = constructTimeSeries(test, look_back)




# convert to dataFrame to view the given array
#testPrint = pd.DataFrame(trainX)
#print testPrint
print trainY.shape[0]

#this is the number of features per timestep as output by the API. 
#as long as the data is being parsed from the above API, this should
#NOT be modified. 
numFeat = 7

#@title Model Parameters:
numNeurons = 4 #@param {type:"integer"}
batches = 2 #@param {type:"integer"}
numEpochs = 25 #@param {type:"integer"}
numLayers = 1 #@param {type:"integer"}

#Default num neurons for LSTM is 4
#Default num batches for LSTM is 1

#Defaults for DNN (8,2)

"""$\Large \text{LSTM Model: }$"""

# reshape input to be [samples, time steps, features]
trainX = np.reshape(trainX, (trainX.shape[0], 1, trainX.shape[1]*numFeat))
testX = np.reshape(testX, (testX.shape[0], 1, testX.shape[1]*numFeat))

# create and fit the LSTM network
modelLSTM = Sequential()
modelLSTM.add(LSTM(numNeurons, input_shape=(1, look_back * numFeat)))
modelLSTM.add(Dense(numFeat))
modelLSTM.compile(loss='mean_squared_error', optimizer='adam')
modelLSTM.fit(trainX, trainY, epochs=numEpochs, batch_size=batches, verbose=2)

# make predictions (here you can choose one of the models)
trainPredictOut = modelLSTM.predict(trainX)
testPredictOut = modelLSTM.predict(testX)

"""## GRU MODEL"""

# reshape input to be [samples, time steps, features]
trainX = np.reshape(trainX, (trainX.shape[0], 1, trainX.shape[1]*numFeat))
testX = np.reshape(testX, (testX.shape[0], 1, testX.shape[1]*numFeat))

# create and fit the GRU model network
modelGRU = Sequential()
modelGRU.add(GRU(numFeat, input_shape=(1, look_back * numFeat)))
for i in range(1,numLayers):
  modelGRU.add(Dense(numFeat))
modelGRU.compile(loss='mean_squared_error', optimizer='adam')
modelGRU.fit(trainX, trainY, epochs=numEpochs, batch_size=batches)

# make predictions (here you can choose one of the models)
trainPredictOut = modelGRU.predict(trainX)
testPredictOut = modelGRU.predict(testX)

"""$\Large \text{Perceptron Model: }$"""

# We add functionality for a multilayer perceptron model (Deep Neural Network)

# reshape input to be [samples, time steps, features]
trainX = np.reshape(trainX, (trainX.shape[0], trainX.shape[1]*numFeat))
testX = np.reshape(testX, (testX.shape[0], testX.shape[1]*numFeat))

modelNN = Sequential()
modelNN.add(Dense(numFeat, input_dim=look_back * numFeat, activation='relu'))
for i in range(1,numLayers):
  modelNN.add(Dense(numFeat))
modelNN.compile(loss='mean_squared_error', optimizer='adam')
modelNN.fit(trainX, trainY, epochs=numEpochs, batch_size=batches, verbose=2)

# make predictions (here you can choose one of the models)
trainPredictOut = modelNN.predict(trainX)
testPredictOut = modelNN.predict(testX)

#@title type "LSTM" or "perceptron", or "GRU" to choose model type:
chosenModel = "perceptron" #@param {type:"string"}

if (chosenModel == 'LSTM'):
  currentModel = modelLSTM
elif (chosenModel == "GRU"):
  currentModel = modelGRU
else:
  currentModel = modelNN



# make predictions (here you can choose one of the models)
trainPredictOut = currentModel.predict(trainX)
testPredictOut = currentModel.predict(testX)

#print trainY.ndim

# invert predictions
trainPredict = scaler.inverse_transform(trainPredictOut)
trainYTrans = scaler.inverse_transform(trainY)

testPredict = scaler.inverse_transform(testPredictOut)
testYTrans = scaler.inverse_transform(testY)

# convert to dataFrame to view the given array
trainingClose = pd.DataFrame(trainYTrans[:,0])
testClose = pd.DataFrame(testYTrans[:,0])

trainPredDF = pd.DataFrame(trainPredict[:,0])
testPredDF = pd.DataFrame(testPredict[:,0])

#We compute the mean squared errors
MSE1 = mean_squared_error(trainY[:,0], trainPredict[:,0])
MSE2 = mean_squared_error(testY[:,0], testPredict[:,0])

print MSE1
print MSE2

# calculate root mean squared error
trainScore = m.sqrt(mean_squared_error(trainYTrans[:,0], trainPredict[:,0]))
print('Train Score: %.2f RMSE' % (trainScore))
testScore = m.sqrt(mean_squared_error(testYTrans[:,0], testPredict[:,0]))
print('Test Score: %.2f RMSE' % (testScore))

"""$\huge\text{Okay so we've trained our model. Now we need to backtest.}$
$\huge\text{We need to decide when we're going to buy and when we're going to sell. }$
$\huge\text{We assume we buy at the close price on day t if we predict the price will rise}$
$\huge\text{by more than } \alpha \text{ where }\alpha \text{ is some pre-specified percent change. }$
$\huge\text{}$

The above criterion will also determine what our classes will be, so we can interpret this as a classification problem and compute accuracy, $F$ measure, and the confusion matrix.
"""

#@title Choose the % change threshold:
alpha = 0.1 #@param {type:"number"}

#trainingClose.describe()

#print list(ETHMinute)
#ETHMinute.iloc[:,0].plot()
originalClose = ETHMinute.iloc[:,0]
list(ETHMinute)
#print headers
#trainPredDF.plot()

origSet = ETHMinute.iloc[:,0].values
#print origSet


trainPredictPlot = np.empty_like(origSet)
trainPredictPlot[:] = np.nan
#print len(trainPredictPlot)
#trainPredictPlot[look_back:len(origSet)+look_back] = trainPredict[:,0]
for i in range(look_back,len(trainPredict[:,0])+look_back):
  trainPredictPlot[i] = trainPredict[i - look_back,0]
  
testPredictPlot = np.empty_like(origSet)
testPredictPlot[:] = np.nan
#print len(testPredict)
#print len(eth)

testPredictPlot[len(trainPredict)+(look_back*2)+1:len(eth)-(2*hold) + 1] = testPredict[:,0]

  
#plt.figure(dpi=300)
#plt.plot(testPredictPlot,linewidth=0.5)
#plt.plot(trainPredictPlot,linewidth=0.5)
#plt.plot(origSet,linewidth=0.5)

stdDev = 9.523417
totalGain = 1
totalFreqGain = 1
   
    
#We compute the buy and hold profit
initialPrice = origSet[len(trainPredict)+(look_back*2)+hold]
endPrice = origSet[len(eth) - 1]
buyHoldGain = ((endPrice - initialPrice)/initialPrice) + 1
buyHoldReturn = buyHoldGain*100 - 100

i = len(trainPredict)+(look_back*2)+hold
while (i < len(eth)):
  freqGain = (origSet[i] - origSet[i - hold])/origSet[i]
  totalFreqGain = totalFreqGain * (1 + freqGain)
  i = i + hold
  
freqReturn = totalFreqGain*100 - 100

totalGain = 1
  
i = len(trainPredict)+(look_back*2)+hold
while (i < len(eth)):
  #the predicted change in percent
  predDelta = (testPredictPlot[i] - testPredictPlot[i - hold])/(testPredictPlot[i])
  predDelta = predDelta*100
  
  
  actualDelta = (origSet[i] - origSet[i - hold])/origSet[i]
  actualDelta = actualDelta*100
  #if the predicted change is greater than a pre-specified threshold
  if (predDelta > alpha):
    gain = (origSet[i] - origSet[i - hold])/origSet[i]
    totalGain = totalGain * (1 + gain)
    
    i = i + hold
  else:
    i = i + 1

returnRate = totalGain*100 - 100

print 'the return rate in percent is: '
print returnRate
print 'the buyHold return rate in percent is: '
print buyHoldReturn
print 'the maxFreq return rate in percent is: '
print freqReturn

"""# We generate a curve that shows the profit/loss as a percent of the principal investment as a function of the chose alpha level. For lack of a better name, we call it the Profit/Loss Operating Characteristic curve, or PLOC curve for short, due to its similarity to a ROC curve for classification problems. Note here that alpha is a threshold for predicted price change as a percent: if our model predicts a price change greater than alpha, we buy, and if not, we do not buy."""

#@title specify range of alpha
startAlpha = -2 #@param {type:"number"}
endAlpha = 2 #@param {type:"number"}
returnRateCurve = []
alphaCurve = []
TPRCurve = []
FPRCurve = []

alpha = startAlpha
while (alpha < endAlpha):
  
  totalGain = 1
  TP = 0
  FN = 0
  FP = 0
  TN = 0

  i = len(trainPredict)+(look_back*2)+hold
  while (i < len(eth) - 1):
    #the predicted change in percent
    predDelta = (testPredictPlot[i] - testPredictPlot[i - hold])/(testPredictPlot[i])
    predDelta = predDelta*100
    predBin = 0
    trueBin = 0
    #if the predicted change is greater than a pre-specified threshold
    if (predDelta > alpha):
      gain = (origSet[i] - origSet[i - hold])/origSet[i]
      totalGain = totalGain * (1 + gain)
      i = i + hold
      predBin = 1
    else:
      i = i + 1
      predBin = -1
    trueDelta = (origSet[i] - origSet[i - hold])/origSet[i]
    trueDelta = trueDelta*100
    if (trueDelta > alpha):
      trueBin = 1
    else:
      trueBin = -1
    if (trueBin == 1 and predBin == 1):
      TP = TP + 1
    if (trueBin == 1 and predBin == -1):
      FN = FN + 1
    if (trueBin == 1 and predBin == -1):
      FN = FN + 1
    if (trueBin == 1 and predBin == -1):
      FN = FN + 1
  


  returnRate = totalGain*100 - 100
  returnRateCurve.append(returnRate)
  alphaCurve.append(alpha)
  
  
  alpha = alpha + 0.05
  
  
  
  #TPR = TP/(TP + FN)
  #FPR = FP/(TN + FP)
  #TPRCurve.append(TPR)
  #FPRCurve.append(FPR)


print returnRateCurve
#ROC = pd.DataFrame(FPRCurve)
##ROC['1'] = pd.DataFrame(TPRCurve)
#ROC.columns = ['FRP','TPR']


returnCurveDF = pd.DataFrame(alphaCurve)
returnCurveDF['1']= pd.DataFrame(returnRateCurve)
returnCurveDF['buy hold'] = buyHoldReturn
returnCurveDF['highFreq'] = freqReturn
#print returnCurveDF

returnCurveDF.columns = ['alpha', 'return rate','buy/hold return rate', 'high freq return rate']



print 'the return rate in percent is: '
print returnRate
print 'the buyHold return rate in percent is: '
print buyHoldReturn
print 'the maxFreq return rate in percent is: '
print freqReturn
returnCurveDF.head(10)
returnCurveDF.plot(x='alpha',y=['return rate','buy/hold return rate','high freq return rate'],title="PLOC curve for " + asset + "/USD",figsize=(18,10))


#returnCurveDF.plot(x='FPR',y=['TPR'],title="ROC curve for " + asset + "/USD",figsize=(18,10))

"""$\Large\text{We generate graphs of the actual price data, the training predictions, and the test predictions: }$"""

plt.figure(dpi=140)
plt.plot(testPredictPlot,linewidth=0.5,label="test predictions")
plt.plot(trainPredictPlot,linewidth=0.5, label='training predictions')
plt.plot(origSet,linewidth=0.5, label="true price")
plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
plotTitle = asset + "/USD " + chosenModel
plt.title(plotTitle)

plt.show()

#red is the actual price graph
#green is the training data predictions after the model is fully trained
#blue is the predictions on the test data

"""# We transform our data from a regression problem into a binary classification problem so that we can apply a wider variety of data mining algorithms to the data. We choose the two classes to be 'price increase' and 'price decrease'."""

#@title We choose a threshold in number of stdDevs 
#to define our binary classes:
beta = 0.05 #@param {type:"number"}
#classDF is our raw dataframe with 7 columns


#we grab just the first column in closeDF
closeDF = classDF[['close']]



#iterate over look_back
for i in range(look_back):
  #copy shifted columns to create time series dataset
  closeDF.loc[:,i] = closeDF.shift(-i)
  
#copy class column
closeDF.loc[:,'class'] = closeDF.shift(- look_back - hold + 1)

#drop original label
closeDF = closeDF.drop(columns=['close'])

#create a dummy copy of the generated dataset
newCloseSet = closeDF.copy()
#compute the standard deviation
stdDevClose = closeDF.std()
closeDF = newCloseSet.copy()
#get numerical variable of stddev
standard = stdDevClose[0]
print len(closeDF)

#keep track of number of positive classes in the dataset
numPosClass = 0
#create classes in the last column, 0 and 1
for i in range(0,len(closeDF)):
  diff = closeDF.loc[i,'class'] - closeDF.loc[i,look_back - 1]
  normDiff = diff/standard
  #print normDiff
  #class is positive if the normed difference is greater than beta
  if normDiff > beta:
    closeDF.loc[i,'class'] = 1
    numPosClass = numPosClass + 1
  else:
    closeDF.loc[i,'class'] = -1
closeDF.head(10)
print numPosClass
#drop last look_back + hold rows since they have NaNs because of our shifts
for i in range(len(closeDF) - look_back - hold + 1, len(closeDF)):
  closeDF = closeDF.drop(i)

closeDF.head(10)

"""# We implement the ADABOOST meta algorithm for binary classification problems. We have an arbitrary classifier function so that we can use several different baseline models, and central AdaBoost algorithm to achieve a lower error rate. We also construct test and training datasets."""

from sklearn.cross_validation import train_test_split

# We define a classification algorithm:

def classify(trainY, trainX, testY, testX, classifier):
    classifier.fit(trainX,trainY)
    preds = classifier.predict(trainX)
    predsTest = classifier.predict(testX)
    denom = float(len(trainY))
    errTrain = sum(preds != trainY) / denom
    errTest = sum(predsTest != testY) / float(len(testY))
    return errTrain, errTest
  
  
np.random.seed(11)
closeDFArray = closeDF.values
closeDFArray = closeDFArray.astype('float32')
# We split into train and test sets
train_size = int(len(closeDFArray) * 0.67)
test_size = len(closeDFArray) - train_size

closeCopy = closeDF.copy()

train = closeCopy.head(train_size)
test = closeCopy.tail(test_size)

trainX, trainY = train.iloc[:,:-1], train.iloc[:,-1]
scaler = MinMaxScaler(feature_range=(0, 1))
trainX = scaler.fit_transform(trainX)
trainX = pd.DataFrame(trainX)
testX, testY = test.iloc[:,:-1], test.iloc[:,-1]
testX = scaler.fit_transform(testX)
testX = pd.DataFrame(testX)



#We define the adaboost function and implement the algorithm

def AdaBoost(trainY, trainX, testY, testX, boostIters, classifier):
    trainSize = len(trainX)
    testSize = len(testX)
    trainingPredictions = np.zeros(trainSize)
    testPredictions = np.zeros(testSize)
    #We create zeroed weights to start with according to the adaboost algorithm
    weights = np.ones(trainSize) / trainSize
    for i in range(boostIters):
      classifier.fit(trainX, trainY, sample_weight = weights)
      ithTrainPreds = classifier.predict(trainX)
      ithTestPreds = classifier.predict(testX)
      #We compute the error expression
      indicatorArray = [int(x) for x in (ithTrainPreds != trainY)]
      weightIndicator = [x if x==1 else -1 for x in indicatorArray]
      error = np.dot(weights, indicatorArray) / sum(weights)
      #We update the weights
      alpha = 0.5 * np.log( (1 - error) / float(error))
      weights = np.multiply(weights, np.exp([float(x) * alpha for x in weightIndicator]))
      #We add to our predictions
      trainingPredictions = [sum(x) for x in zip(trainingPredictions, [x * alpha for x in ithTrainPreds])]
      testPredictions = [sum(x) for x in zip(testPredictions, [x * alpha for x in ithTestPreds])]
    #Make output binary
    trainingPredictions = np.sign(trainingPredictions)
    testPredictions = np.sign(testPredictions)
    #Compute final error
    errTrain = sum(trainingPredictions != trainY) / float(len(trainY))
    errTest = sum(testPredictions != testY) / float(len(testY))
    #return final error
    
    return errTrain, errTest

#@title Choose a classification model (tree, svm, naivebayes, linear), and the number of boosting iterations:

#@title Iterations (50-400):
iterations = 200 #@param {type:"integer"}
#We use a plotting function:
def plotErr(trainErr, testErr):
    error = pd.DataFrame([trainErr, testErr]).T
    error.columns = ['Training', 'Test']
    plot1 = error.plot(linewidth = 3, figsize = (8,6),color = ['lightblue', 'darkblue'], grid = True)
    plot1.set_xlabel('Number of iterations', fontsize = 12)
    plot1.set_xticklabels(range(0,iterations,10))
    plot1.set_ylabel('Error rate', fontsize = 12)
    plot1.set_title('Error rate vs number of iterations', fontsize = 12)
    plt.axhline(y=testErr[0], linewidth=1, color = 'red', ls = 'dashed')



from sklearn.svm import SVC
from sklearn import linear_model
from sklearn.tree import DecisionTreeClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis


#We initialize several different classifiers
tree = DecisionTreeClassifier(max_depth = 3, random_state = 1)
svm = SVC(gamma=2, C=1)
naivebayes =  GaussianNB()
quad = QuadraticDiscriminantAnalysis()
linear = linear_model.SGDClassifier()


classModel = naivebayes #@param {type:"raw"}

unboostedError = classify(trainY, trainX, testY, testX, classModel)
trainErr = [unboostedError[0]]
testErr = [unboostedError[1]]


for i in range(10, iterations, 10):
  ithErr = AdaBoost(trainY, trainX, testY, testX, i, classModel)
  trainErr.append(ithErr[0])
  testErr.append(ithErr[1])
  print i
  
plotErr(trainErr,testErr)



