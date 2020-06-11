import multiprocessing as mp
import time
import matplotlib; matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import math
import numpy as np

def primes(x):
    c=0
    for num in range(1, x):
        for i in range(2, num):
            if num % i == 0:
                break
        else:
            c+=1
    return c

def par(pars):
    x=pars[0]
    p=pars[1]
    c=int(3000000000/x)
    num=(p-1)*c
    while num<=p*c:
        #sr=math.sqrt(num)
        sr=num*num
        num+=1
    return sr

def calc(x):
    r = [0]*10
    for i in range(len(r)):
        #r[i]=1
        r[i] = math.sqrt(math.e**(math.atan(math.sin(x*math.pi*math.pi))))/(math.sqrt(2*math.pi)*math.sqrt(x))
    return sum(r)

def par1(pars):
    x=pars[0]
    p=pars[1]
    c=int(10000000/x)
    vcalc = np.vectorize(calc)
    npar = np.random.rand(c)
    return vcalc(npar)

start = time.time()
c=par1([1,1])
dtseq = time.time()-start
print "Process time: %5.1f for Sequential"%dtseq
speeduplist=[]

procsl=[]
for procs in range(2,61):
    if procs % 2 != 0:
        continue
    procsl.append(procs)
    params=[]
    for i in range(1,procs+1):
        params.append([procs, i])
    #print params
    pool=mp.Pool(processes=procs)
    start = time.time()
    res = pool.map(par1, params)
    #res = mp.Pool.apply_async(primes, params)
    pool=None
    dt = time.time()-start
    print "Process time: %5.1f for %d processes"%(dt, procs)
    speeduplist.append(dtseq/dt)

plt.figure()
plt.plot(procsl, speeduplist)
#plt.axis([0, 100, 0, 1])
plt.ylabel('Speed up')
plt.xlabel('PUs')
plt.show()
i=1

#print primes(1000)   
