import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

retry_strategy = Retry(
    total=5,  # 总重试次数
    status_forcelist=[429, 500, 502, 503, 504],  # 指定哪些状态码需要重试
    method_whitelist=["HEAD", "GET", "OPTIONS"],  # 指定哪些请求方法需要重试
    backoff_factor=1  # 重试回退策略
)

adapter = HTTPAdapter(max_retries=retry_strategy)
http = requests.Session()
http.mount("https://", adapter)
http.mount("http://", adapter)

response = http.get('https://192.168.31.218.com')
