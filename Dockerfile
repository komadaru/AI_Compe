# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# # システム依存関係をインストール
# RUN apt-get update && apt-get install -y \
#     build-essential \
#     libatlas-base-dev \
#     gfortran \
#     && apt-get clean \
#     && rm -rf /var/lib/apt/lists/*

# 必要な依存関係を事前にインストール
RUN pip install --no-cache-dir numpy pandas scikit-learn torch torchvision

# # Install dependencies
# COPY requirements2.txt ./
# RUN pip install --no-cache-dir -r requirements2.txt
# 提出コードと実行スクリプトをコピー
COPY submitted_code.py .
COPY run_code.py .

# Copy the current directory contents into the container at /app
COPY . /app

# Define the command to run the application
CMD ["python", "watchdog.py"]
