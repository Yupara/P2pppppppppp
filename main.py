import sys
print(sys.path)  # Посмотрите, есть ли /app в путях
import os
print(os.listdir("/app"))  # Посмотрите, есть ли database в /app
print(os.listdir("/app/database"))  # Посмотрите содержимое database
