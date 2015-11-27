# 
# requires numpy and scipy
import random ## MODIFY HERE
import numpy
import math
import scipy
from scipy.special import binom

def lap(scale):
    return numpy.random.laplace(0,scale) 

def normal(scale):
    return numpy.random.normal(0,scale)

def mean(a):
    return sum(a)/float(len(a))


class Datasets:
        # Randomly split 
    def splitDB(self,database, p=0.5):
        random.seed()
        random.shuffle(database)  # Randomly permute the database
        testSize = int(math.ceil(p*len(database)))
        privDB = database[:testSize] # Take the first p fraction for the private DB
        pubDB = database[testSize:] # and the remainder for the public DB
        return (pubDB,privDB)
        
    def applyCountQuery(self,query, db):
        return mean([max(min(query(x),1),0) for x in db])  #The mean value of the query, truncated to take values in [0,1], on the database.
            
    def __init__(self, database, testFraction=0.5, answerPrecision=2):
        self.db = database
        self.p = testFraction
        (self.pubDB, self.privDB) = self.splitDB(self.db,self.p) # Split database into public and private portion


# SparseVector for private and non-private
class SparseVector:   
    #Get width of confidence interval of next counting query, with covergae probability coverageP. Returns tau such that confidence interval is answer +- tau
    # If the last answer wasPrivate, the confidence interval comes just from a Chernoff bound. Otherwise, it is the sum of the Chernoff bound (which gives a
    # confidence interval around the answer of the query on privDB, plus the threshold.)
    def getConfidenceWidth(self, coverageP=0.95, wasPrivate=False):
        n = len(self.data.privDB)        
        if self.diff_priv:
            DPWidth = max(2.0*self.budget/(self.scale*n),math.sqrt(math.log(6/(1-coverageP))/n)) # equation DP_width, See TeX document.
            if wasPrivate:        
                return DPWidth  # If the last answer as private, the Chernoff bound gives the correct width.
            else:
                return DPWidth + self.T +self.scale*math.log(1/(1-coverageP)) # Otherwise, we need to add the threshold as well.  
        else:
            numTranscripts = 2**self.answerPrecision*self.budget 
            descriptWidth = math.sqrt(3*math.log(2*numTranscripts/(1-coverageP))/(n)) # equation descript_width, See TeX document.      
            if wasPrivate:        
                return descriptWidth  # If the last answer as private, the Chernoff bound gives the correct width.
            else:
                return descriptWidth + self.T  # Otherwise, we need to add the threshold as well.  
            
    def answerQuery(self, query):
        if self.budget - self.aboveThresholdCounter <= 0:
            self.proceed = False            
            return "No more questions allowed"
        else:
            self.queryCounter += 1  # We have answered one more query
            pubAnswer = self.db.applyCountQuery(query, self.db.pubDB)  # Evaluate query on public database        
            privAnswer = self.db.applyCountQuery(query, self.db.privDB) # Evaluate query on private database
            if self.diff_priv:
                belowThresh = abs(privAnswer - pubAnswer) <= self.T + lap(4.0*self.scale)
            else:
                belowThresh = abs(privAnswer - pubAnswer) <= self.T
                self.decimalsOutput += self.answerPrecision  # We answered it with this many digits of precision
            if belowThresh:
                self.lastQueryWasPrivate = False  # If answers are close, return public answer
                return pubAnswer
            else:  # Otherwise, return private answer
                self.aboveThresholdCounter+=1  # This was an above threshold query; count it. 
                self.T = self.getConfidenceWidth() + lap(2.0*self.scale) # Add fresh noise
                self.lastQueryWasPrivate = True
                print "private answer ",self.aboveThresholdCounter
                if self.diff_priv:
                    return privAnswer+lap(self.scale) # Return answer with noise
                else:
                    return int(privAnswer*10**self.answerPrecision)/float(10**self.answerPrecision)  # Return answer with the right number of decimals of precision

    def __init__(self, database, budget = 10, answerPrecision=2, sigma = 0):
        self.aboveThresholdCounter = 0 # Initialize count of how many above threshold queries we have seen
        self.queryCounter = 0 # Initialize count of how many queries we have seen
        self.decimalsOutput = 0 # Initialize count of total number of decimal places of output we have answered using the private database
        self.data = database  
        self.budget = budget
        self.T = 0 # Initialize threshold
        self.lastQueryWasPrivate = False # Was the last query answered with the private database?
        self.diff_priv = sigma>0 # If we want a DP answer
        self.db = database
        self.proceed = True
        self.answerPrecision = answerPrecision # How many decimal places to report answers
        if self.diff_priv:
            self.scale = sigma # For counting queries the sensitivity is one
            self.T = self.getConfidenceWidth() + lap(2.0*self.scale)  # Set threshold to be 95% confidence interval for counting query + Noise
        else:
            self.T = self.getConfidenceWidth() # Set threshold to be 95% confidence interval for counting query
            
    

# Example usage
exampleDB= [i for i in range(10000)] # database with integer entries. (here just the integers from 0 to 9999)
data = Datasets(exampleDB, 0.8) # create an instance of the SafeAnalysis object, instantiated with the example database. We are allocating 80% of the data to the private DB, and the remaining 20% goes to the publicDB

def parity(x):     # Define an example query: parity just evaluates whether the integer is even or odd. 
    return x % 2

sparsevect = SparseVector(data,budget = 2) #sparsevect = SparseVector(data,budget = 2, sigma = .1)
            
myQueryAnswer = sparsevect.answerQuery(parity) # Get the answer to this query
 
if sparsevect.proceed: 
    print "My query had answer: ",myQueryAnswer , " +- ",sparsevect.getConfidenceWidth(0.95,sparsevect.lastQueryWasPrivate)
else:
    print myQueryAnswer
                                                        
if sparsevect.lastQueryWasPrivate:
    print "In fact, it was answered on the private database."
else:
    print "In fact, it was answered on the public database."
    
    
#print "I'm going to answer a parity query now."
#print "If it is answered on the private database, the 95% confidence interval around this answer will be +- ",sparsevect.getConfidenceWidth(0.95,True)
#print "If it is answered on the public database, the 95% confidence interval around the answer will be +- ",sparsevect.getConfidenceWidth(0.95,False)    


