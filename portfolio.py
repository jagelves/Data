# Author: J. Alejandro Gelves
# Title: Creating an optimal portfolio using the NASDAQ


# Start by loading the required packages
import numpy as np
import mysql.connector
import pandas as pd
from gurobipy import *

# Creating the Gurobi optimization model
m = Model("Investments")
m.ModelSense = GRB.MINIMIZE
m.setParam("TimeLimit", 7200)

# Establishing the SQL connection to get the data
db=mysql.connector.connect(host='localhost',user='root',passwd='',database='nasdaq')
cur=db.cursor()

# Get the returns
cur.execute('SELECT meanReturn FROM nasdaq.r')
returns=cur.fetchall()
returns=np.matrix(returns)
maxreturns = float(max(returns))
minreturns = float(min(returns))

# Loading in the Stock names
cur.execute('SELECT stock FROM nasdaq.r')
stocks=cur.fetchall()
stock=[]
for i in stocks:
  for a in i:
    stock.append(a)

# Import covariance data
cur.execute('SELECT * FROM nasdaq.cov')
cov=cur.fetchall()
n = len(cov)
cov=np.matrix(cov)
covmatrix=np.zeros((int(cov[n-1,0]),int(cov[n-1,1])))
print(cov[1,0])
for i in range(0,n):
    j=int(cov[i,0])-1
    k=int(cov[i,1])-1
    covmatrix[j,k]=float(cov[i,2])
    covmatrix[k,j]=covmatrix[j,k]

# uploading multiple variables to optimize. The fraction of each stock that should be held.
variables = pd.Series(m.addVars(stock,vtype=GRB.CONTINUOUS,lb=0.0,ub=1.0), index=stock)
m.update()

# Creating a numpy matrix for the fractions of investments. Creating the expected profit.
fractions=np.matrix(variables)
sfractions=sum(fractions).item(0)
exprofit=fractions*returns

# Creating the objective function
objrisk=fractions*covmatrix*np.transpose(fractions)

portfolio=[]
iterations = 20
targets=np.arange(minreturns,maxreturns,(maxreturns -minreturns)/iterations)
for i in targets:
  # Add the constraints
  m.addConstr(variables.sum() == 1, "Budget")
  m.addConstr(exprofit.item(0), GRB.GREATER_EQUAL, i, "ExpProfit")
  
  # The objective function
  m.setObjective(objrisk.item(0), GRB.MINIMIZE)
  m.update()
  m.optimize()
  portfolio.append([i,m.getObjective().getValue()])
  cur.execute("insert into portfolio (expReturn, expRisk) values (%s, %s)",(float(i) ,float(m.getObjective().getValue()))) # what we send to the db using tuples and place holders

db.commit()

cur.close()  
db.close()
