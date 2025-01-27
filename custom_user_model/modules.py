import time
from datetime import timedelta
from django.contrib.auth import logout

def get(number):
    num = 2323232
    return num > number

exp_time = time.time()

print(get(5767), exp_time)
exp_time = timedelta()
print(exp_time)

def loggingout(request):
    try:
        logout(request)
        print('yep')
    except Exception as e:
        print('nope')