#!/bin/bash
echo "🚀 Building QuotexSignalNet System"

echo "🔧 Installing TA-Lib..."
wget https://github.com/TA-Lib/ta-lib/archive/refs/tags/v0.4.0.tar.gz
tar -xzvf v0.4.0.tar.gz
cd ta-lib-0.4.0/
./configure --prefix=/usr
make
make install
cd ..
rm -rf v0.4.0.tar.gz ta-lib-0.4.0

echo "🐍 Installing Python packages..."
pip install -U pip
pip install -r requirements.txt

echo "✅ Build completed"
