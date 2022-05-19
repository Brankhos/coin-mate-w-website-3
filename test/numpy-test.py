import numpy as np


aa = np.array([[6545421,645123,654132,54312],[523,5449,63321,654564]])

cc = aa[:,0] < 600

aa = aa[cc]
print(cc)
print(aa)